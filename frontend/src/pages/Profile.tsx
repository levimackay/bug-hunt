import { fetchProfile } from "../api/profile";
import { useAsync } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { SkillBar } from "../components/SkillBar";
import { TopBar } from "../components/TopBar";

export function Profile() {
  const state = useAsync(fetchProfile, []);

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Profile" />
      <div className="flex-1 overflow-auto">
        <AsyncBoundary state={state}>
          {(profile) => (
            <div className="mx-auto max-w-2xl px-6 py-8">
              <h1 className="mb-6 text-xl font-medium text-ink">Profile</h1>

              <div className="mb-6 flex gap-3">
                <div className="flex-1 border border-border bg-surface px-4 py-3">
                  <div className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                    Level
                  </div>
                  <div className="mt-1 font-mono text-2xl text-ink">{profile.level}</div>
                </div>
                <div className="flex-1 border border-border bg-surface px-4 py-3">
                  <div className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                    Total XP
                  </div>
                  <div className="mt-1 font-mono text-2xl text-ink">
                    {profile.totalXp.toLocaleString()}
                  </div>
                </div>
              </div>

              <section className="border border-border bg-surface p-4">
                <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                  Skills
                </h2>
                {profile.skills.length === 0 ? (
                  <p className="text-sm text-ink-faint">
                    No skills tracked yet — resolve an investigation to start building mastery.
                  </p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {profile.skills.map((skill) => (
                      <SkillBar key={skill.name} name={skill.name} masteryPct={skill.masteryPct} />
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}
        </AsyncBoundary>
      </div>
    </div>
  );
}
