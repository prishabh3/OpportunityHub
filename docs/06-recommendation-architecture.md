# OpportunityHub — Recommendation & AI Architecture

## 1. Components

1. **Resume Analyzer** — parses an uploaded resume into structured data.
2. **Embedding Pipeline** — turns opportunities and user profiles into vectors for semantic
   similarity.
3. **Recommendation Engine** — hybrid scoring (vector similarity + rule-based signals) producing
   `opportunity_matches`.
4. **Semantic Search** — natural-language query → structured filters + vector search.

All LLM calls go through a single `app/infrastructure/ai/llm_client.py` abstraction so the
provider (Anthropic Claude / OpenAI) can be swapped via config without touching call sites.

## 2. Resume Analyzer

**Input**: uploaded PDF/DOCX → stored in Supabase Storage (`resumes/{user_id}/{uuid}.pdf`).

**Pipeline** (`analyze_resume` Celery task):

1. Extract raw text (`pypdf` / `python-docx`).
2. LLM structured extraction with a strict JSON schema (via Pydantic + function-calling /
   structured output):
   ```json
   {
     "skills": ["Python", "React", "PostgreSQL", ...],
     "projects": [{"name": "...", "description": "...", "technologies": [...]}],
     "experience": [{"title": "...", "company": "...", "duration_months": 6, "description": "..."}],
     "education": [{"degree": "...", "institution": "...", "graduation_year": 2026}]
   }
   ```
3. Persist to `resume_analyses`. Update `profiles.user_skills` (upsert skills from the
   extraction, marking them `source='resume'` so manual edits aren't overwritten).
4. Enqueue `embed_profile.delay(user_id)` to refresh `profiles.profile_embedding`.

## 3. Match Score (Resume vs. Opportunity)

`GET /api/v1/opportunities/{id}/match` computes/returns:

```json
{
  "match_score": 78.5,
  "missing_skills": ["Kubernetes", "Go"],
  "resume_suggestions": [
    "Highlight your distributed-systems coursework — this role emphasizes scale.",
    "Add a project demonstrating Go experience if you have any."
  ],
  "probability_estimate": "medium"
}
```

Computation (`compute_match_score`):

- **Skill overlap (40%)**: Jaccard similarity between `user_skills` and `details.requirements`
  (requirements are tagged against the `skills` taxonomy during normalization where possible).
- **Semantic similarity (40%)**: cosine similarity between `profile_embedding` and
  `opportunity.embedding` (captures fit beyond exact keyword overlap — e.g. "ML" vs "deep
  learning").
- **Preference alignment (20%)**: bonuses for matching `preferred_companies`,
  `preferred_countries`, `preferred_role`, `remote_type`, and graduation-date vs. internship
  timing.
- `missing_skills` = top requirements not present in `user_skills` ∩ resume skills.
- `resume_suggestions` and `probability_estimate` (`low`/`medium`/`high`, derived from
  `match_score` buckets + missing-skill count) come from a short LLM call given the score
  breakdown — kept optional/cacheable since it's the expensive part.
- Cached in `opportunity_matches`, recomputed when: resume re-analyzed, profile updated, or
  opportunity `details`/`embedding` changes (invalidation via `computed_at` vs.
  `opportunities.updated_at`/`profiles.updated_at`).

## 4. Embedding Pipeline

- Model: configurable (default a 1536-dim embedding model, e.g. OpenAI
  `text-embedding-3-small` or a self-hosted alternative — abstracted behind
  `EmbeddingClient.embed(text: str) -> list[float]`).
- **Opportunity embedding input**: `f"{title}\n{organizer}\n{description}\n{tags}\n{details}"`
  (truncated to model context).
- **Profile embedding input**: concatenation of `user_skills`, resume `skills`/`projects`/
  `experience` summaries, and titles of bookmarked opportunities (recency-weighted — last 20
  bookmarks).
- Recompute triggers:
  - Opportunity: on create, and on update only if `content_hash` changed.
  - Profile: on resume re-analysis, on skill list edit, on every Nth bookmark (batched, not
    per-bookmark, to avoid thrash) via a debounced Celery task
    (`embed_profile.apply_async(countdown=300)`, deduped by Redis key).

## 5. Recommendation Feed

`GET /api/v1/recommendations`:

```sql
select o.* from opportunities o
join opportunity_matches m on m.opportunity_id = o.id and m.user_id = :user_id
where o.status = 'active'
order by m.match_score desc, o.deadline_at asc nulls last
```

- `opportunity_matches` is populated incrementally:
  - When a new opportunity is ingested → scored against all users with a `profile_embedding`
    (batched nightly for users not flagged "active recently"; immediate for active users via
    the `evaluate_notifications` pipeline step which doubles as match computation).
  - When a user updates their profile/resume → recompute against recent opportunities
    (last 90 days, `status='active'`), via `POST /recommendations/refresh`.
- Cold start (no resume/skills): fall back to `preferred_role`/`preferred_companies` rule-based
  filtering + "trending" opportunities, with a UI prompt to upload a resume / add skills.

## 6. Semantic Search

`GET /api/v1/search?q=...`:

1. **Query parsing** (LLM, structured output): extract `{ type?, tags?, country?, remote_type?,
   prize_min?, deadline_before?, free_text_remainder }` from the natural-language query.
   - "AI internships in Europe" → `{type: internship, tags: [ai], country: <EU list>}`
   - "Hackathons with prize > $10,000" → `{type: hackathon, prize_min: 10000}`
   - "Remote backend internships" → `{type: internship, remote_type: remote, tags: [backend]}`
2. **Retrieval**: apply extracted structured filters as a SQL `WHERE`, then:
   - If `free_text_remainder` is non-empty → embed it and rank candidates by cosine similarity
     to `opportunities.embedding` (pgvector `<=>` operator).
   - Else → Meilisearch keyword search for ranking within the filtered set (faster, good for
     "Google AI"-style brand/keyword queries).
3. **Fallback**: if the LLM parser fails/times out (budget: 1.5s), skip straight to Meilisearch
   full-text search on `q` with no structured filters — search must never hard-fail due to LLM
   unavailability.
4. Log `{query, parsed_filters}` to `search_history` for authenticated users (feeds future
   recommendation personalization).

## 7. Cost & Performance Controls

- All LLM calls are async, time-boxed, and results cached (resume analysis keyed by file hash;
  query parsing cached in Redis keyed by normalized query string, TTL 1h).
- Embedding generation batched (connector pipeline batches up to 50 opportunities per
  embedding API call).
- Feature flag `AI_FEATURES_ENABLED` allows running the platform with recommendations degraded
  to rule-based-only (no LLM/embedding calls) for cost-constrained environments.
