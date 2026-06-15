"use client";

import { motion } from "framer-motion";
import {
  Bell,
  Calendar,
  FileSearch,
  Sparkles,
  Bookmark,
  SlidersHorizontal,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    icon: Sparkles,
    title: "Continuous aggregation",
    description:
      "Isolated connectors pull from Google, Microsoft, Amazon, Devpost, MLH, Unstop, YC, and more — deduplicated and normalized into one feed.",
  },
  {
    icon: SlidersHorizontal,
    title: "Real filters that matter",
    description:
      "Filter by type, tags, country, remote/hybrid/onsite, difficulty, and prize pool — across hackathons, internships, jobs, and research programs.",
  },
  {
    icon: FileSearch,
    title: "Resume-aware matching",
    description:
      "Upload your resume to get a match score, missing-skill breakdown, and tailored suggestions for every opportunity.",
  },
  {
    icon: Bell,
    title: "Deadline intelligence",
    description:
      "Get notified 7 days and 24 hours before a deadline — and immediately if a deadline changes — via email, Discord, Telegram, or push.",
  },
  {
    icon: Bookmark,
    title: "Bookmarks & folders",
    description:
      "Organize opportunities into folders with notes and tags, and export everything to your calendar via ICS or Google Calendar sync.",
  },
  {
    icon: Calendar,
    title: "Personalized dashboard",
    description:
      "Upcoming deadlines, recommended opportunities, recently added, and trending — tailored to your skills and preferences.",
  },
];

export function FeatureGrid() {
  return (
    <section id="features" className="px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            An intelligence platform, not another job board
          </h2>
          <p className="mt-4 text-muted-foreground">
            The hard part isn&apos;t showing listings — it&apos;s keeping them fresh,
            deduplicated, and relevant to you.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.4, delay: i * 0.05, ease: "easeOut" }}
            >
              <Card className="h-full border-border/60 bg-card/50 transition-colors hover:border-border">
                <CardHeader>
                  <div className="mb-2 flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <feature.icon className="size-4.5" />
                  </div>
                  <CardTitle className="text-base">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
