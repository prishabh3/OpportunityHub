import type { Metadata } from "next";

import { Navbar } from "@/components/layout/navbar";
import { ProfileForm } from "@/features/profile/components/profile-form";

export const metadata: Metadata = { title: "Profile — OpportunityHub" };

export default function ProfilePage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-xl px-4 py-12">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight">Your profile</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            This powers your personalized recommendations and matching.
          </p>
        </div>
        <ProfileForm />
      </main>
    </>
  );
}
