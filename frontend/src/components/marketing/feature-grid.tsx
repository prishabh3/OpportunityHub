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
    title: "Always-fresh listings",
    description:
      "Live connectors pull hundreds of real hackathons and jobs from Devpost, Unstop, and company boards like Stripe, Databricks, and Anthropic — deduplicated and refreshed automatically.",
  },
  {
    icon: SlidersHorizontal,
    title: "Filters that actually help",
    description:
      "Narrow by category, type, experience level (intern → senior), remote / hybrid / onsite, and country — then search across everything full-text.",
  },
  {
    icon: FileSearch,
    title: "Matched to your profile",
    description:
      "Add your skills and preferences and every opportunity gets a match score — so the most relevant ones rise to the top of your dashboard.",
  },
  {
    icon: Bell,
    title: "Deadline reminders",
    description:
      "Bookmark anything and get an in-app reminder as its deadline approaches, so nothing slips by unnoticed.",
  },
  {
    icon: Bookmark,
    title: "Save what matters",
    description:
      "One click to bookmark an opportunity from any list, and find everything you've saved in one place.",
  },
  {
    icon: Calendar,
    title: "Your dashboard",
    description:
      "A personalized home that surfaces opportunities recommended for you, with quick access to your bookmarks and profile.",
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
