# PRD (EN) — Project Solo Levelling (PSL)

## Product Requirements Document: Real-Life RPG Self-Improvement App

## 1. Product Overview

This product is a gamified self-improvement platform where users log real-life activities to increase personal stats, gain XP, level up, and track their personal growth as if their life were an RPG.

The core idea is:

> Turn your real life into an RPG where your habits level up your character.

The product is not just a habit tracker. It is an identity-driven progression system that helps users feel that they are becoming stronger in real life.

---

## 2. Problem Statement

Many people want to improve their lives through exercise, learning, better sleep, better habits, and reduced negative behaviors, but traditional habit trackers often feel boring, repetitive, or emotionally disconnected.

Users often lose motivation because progress is not visible enough. They may perform positive actions in real life, but they do not receive immediate emotional feedback or a sense of growth.

This product solves that problem by turning real-life activities into visible character progression through stats, XP, levels, and future gamification systems.

---

## 3. Product Goals

### MVP Goals

The MVP should prove that users enjoy logging real-life actions and seeing their stats grow.

Primary goals:

- Allow users to create an account.
- Allow users to log positive and negative real-life activities.
- Increase or decrease stat XP based on logged actions.
- Show user stats with XP bars and levels.
- Show global user level.
- Provide a dark futuristic dashboard.
- Allow admins to configure available logs and their stat effects.
- Keep logging fast and simple.

### Long-Term Goals

Future versions may include:

- Achievements.
- Streaks.
- Daily quests.
- Daily rankings.
- Weekly summaries.
- Character visual evolution.
- Friends and multiplayer.
- Leaderboards.
- Calories and macro tracking.
- AI-generated insights.
- Comeback quests.
- Monetization.
- Avatars and cosmetics.

---

## 4. Target Audience

The initial target audience is not fully researched yet.

For the MVP, the first users are expected to be Davyd and his friends: people who are interested in self-improvement, gaming, productivity, and personal growth.

Potential broader audience:

- Gamers interested in self-improvement.
- People with productivity or habit-building goals.
- Young adults interested in “monk mode”, fitness, learning, and lifestyle optimization.
- Users who find normal habit trackers boring.

---

## 5. Product Positioning

The product should be positioned as:

> A real-life RPG for self-improvement.

It should feel like a combination of:

- Habit tracker.
- Life dashboard.
- RPG stat system.
- Self-development identity system.

The emotional promise is:

> “I am evolving into my ideal self.”

---

## 6. Core User Experience

### MVP Core Loop

1. User performs a real-life action.
2. User opens the app.
3. User logs the action.
4. The app applies predefined XP changes.
5. Stats increase or decrease.
6. User sees updated XP bars and levels.
7. User feels visible progress.

### Future Core Loop

1. User completes actions or habits.
2. User gains XP and stat progress.
3. User maintains streaks.
4. User completes quests.
5. User earns achievements.
6. User unlocks titles, visuals, or rewards.
7. User compares progress with friends.
8. User continues building their real-life character.

---

## 7. Core Stats

The MVP should include the following stats:

| Stat          | Meaning                                            |
| ------------- | -------------------------------------------------- |
| Strength      | Training, gym, sport, physical activity            |
| Health        | Sleep, nutrition, water, healthy behavior          |
| Intelligence  | Learning, books, English, courses                  |
| Mental State  | Meditation, walks, rest, recovery                  |
| Endurance     | Cardio, steps, long physical effort                |
| Finance       | Saving money, income, investments                  |
| Social Skills | Meetings, new people, calls with family or friends |

Stats are symbolic but should feel emotionally believable.

---

## 8. User Stories and Use Cases

### User Story 1: Log Positive Activity

As a user, I want to log a positive real-life action so that my stats increase and I feel progress.

Example:

- User logs “1 hour gym training”.
- Strength increases.
- Health may also increase.
- Global XP increases.

### User Story 2: Log Negative Activity

As a user, I want to log a negative action so that my character reflects my real-life behavior.

Example:

- User logs “10 hours TikTok scrolling”.
- Intelligence or mental state decreases.
- The system should not shame the user.

### User Story 3: View Character Progress

As a user, I want to see my stats, XP bars, and level so that I understand my current character progression.

### User Story 4: Admin Configures Logs

As an admin, I want to create and configure available log types so that the product can be balanced without code changes.

Example:

- “Workout 1 hour” gives +10 Strength XP and +5 Health XP.
- “Alcohol” gives -5 Health XP.

---

## 9. Functional Requirements

### 9.1 Authentication

Must-have:

- User can register.
- User can log in.
- User can log out.
- User has a personal profile.

### 9.2 Profile Dashboard

Must-have:

- Show username.
- Show global user level.
- Show all core stats.
- Show XP progress bar for each stat.
- Show current level for each stat.
- Show recent logs.

Should-have:

- Dark futuristic UI.
- Basic animation when XP changes.
- Level-up modal with confetti.

### 9.3 Logging System

Must-have:

- User can select a predefined log.
- User can submit a log.
- Logs can be positive or negative.
- Logs can affect one or multiple stats.
- Logs may be binary or quantified depending on the activity.

Examples:

- Binary: “Had breakfast”.
- Quantified: “Gym workout — 60 minutes”.

### 9.4 XP and Level System

Must-have:

- Each stat has XP.
- Each stat has a level.
- User has a global level.
- Logging actions changes XP.
- Positive logs increase XP.
- Negative logs decrease XP.
- If XP decreases enough, level may decrease in MVP.

Should-have:

- Early levels should be fast.
- Later levels should become harder.
- XP values should be configurable by admins.

Future:

- Diminishing returns.
- Daily caps.
- Condition system instead of direct level loss.
- More advanced progression formulas.

### 9.5 Admin Panel

Must-have:

- Admin can create predefined logs.
- Admin can edit predefined logs.
- Admin can define which stats each log affects.
- Admin can define XP value for each affected stat.
- Admin can define whether the log is positive or negative.

Should-have:

- Admin can disable or enable logs.
- Admin can manage stat balancing.

### 9.6 Theme

Must-have:

- Dark mode by default.
- Futuristic/cyberpunk-inspired visual style.

Should-have:

- Light mode option.

---

## 10. Non-Functional Requirements

### Performance

- Logging should feel instant.
- Main dashboard should load quickly.
- XP and level updates should be visible immediately after logging.

### Usability

- User should be able to log an action in around 30 seconds.
- The app should not feel like work.
- The app should avoid complex forms in MVP.

### Scalability

- The product should support future features such as achievements, quests, leaderboards, AI insights, and social systems.

### Security

- User data should be private.
- Authentication should be secure.
- Admin functionality should be protected by role-based access.

### Platform

- MVP should be a web app with PWA support.
- Future versions may include native mobile apps.

---

## 11. Assumptions

- Users will be willing to manually log activities in the MVP.
- Early users will understand XP, stats, and levels.
- The first audience will be motivated by self-improvement and RPG-style progression.
- Admin-configured balancing is enough for MVP.
- Social features are not required to validate the core idea.
- Achievements, streaks, and quests can be added after the core loop is validated.

---

## 12. Constraints

- MVP should stay simple.
- No AI in MVP.
- No achievements in MVP.
- No streaks in MVP.
- No leaderboards in MVP.
- No calories system in MVP.
- No full avatar system in MVP.
- No complex anti-cheat system in MVP.
- No advanced technical implementation details should be included in this PRD stage.

---

## 13. Prioritization: MSCW

### Must-have

- Account system.
- User profile.
- Core stats.
- XP system.
- Global level.
- Manual logs.
- Positive and negative log effects.
- Admin-configured logs.
- Dark futuristic dashboard.

### Should-have

- Level-up modal.
- Confetti animation.
- Light mode.
- Recent activity history.
- Basic mobile/PWA optimization.
- Basic analytics.
- Log categories.

### Could-have

- Simple onboarding.
- Achievements.
- Custom usernames.
- Monetization.
- Macros.
- Calories.

### Won’t-have for MVP

- Streaks.
- Quests.
- Leaderboards.
- Friends.
- AI coach.
- Avatars.
- Marketplace.
- Better animations.
- Complex anti-cheat system.

---

## 14. Acceptance Criteria

The MVP is considered successful when:

- User can register and log in.
- User can view their profile dashboard.
- User can see all seven stats.
- User can submit positive and negative logs.
- Logs correctly update XP.
- Stat levels update based on XP.
- Global user level updates based on progress.
- Admin can create and edit predefined logs.
- Logging takes less than 30 seconds.
- The UI clearly communicates RPG-style progression.
- The app works as a PWA or mobile-friendly web app.

---

## 15. Timeline and Milestones

### Phase 1: Product Foundation

- Finalize PRD.
- Define MVP scope.
- Define core stats.
- Define initial predefined logs.
- Define basic XP/level rules.

### Phase 2: MVP Design

- Create dashboard wireframes.
- Create logging flow.
- Create admin panel wireframes.
- Define dark futuristic UI direction.

### Phase 3: MVP Development

- Build authentication.
- Build user profile.
- Build stats system.
- Build logging system.
- Build admin panel.
- Build XP and level logic.

### Phase 4: Testing

- Test log creation.
- Test stat updates.
- Test level changes.
- Test negative logs.
- Test mobile/PWA experience.
- Test UX with initial users.

### Phase 5: MVP Release

- Release to Davyd and friends.
- Collect feedback.
- Measure whether users actually log actions.
- Identify what feels fun, boring, or confusing.

---

## 16. Dependencies

- Product owner decisions on initial logs and XP values.
- Designer for cyberpunk-style dashboard.
- Developer implementation of account, logging, XP, and admin systems.
- Admin panel for balancing logs.
- Early user feedback from Davyd and friends.
- Future mobile/PWA support.

---

## 17. Risks and Mitigation

### Risk 1: App feels like a spreadsheet

Mitigation:

- Keep logging fast.
- Use XP bars, levels, animations, and visual feedback.
- Avoid too much manual input.

### Risk 2: Progression feels fake

Mitigation:

- Keep XP values emotionally believable.
- Use admin balancing.
- Add diminishing returns later.

### Risk 3: Users feel punished

Mitigation:

- Avoid shameful wording.
- Use neutral language for negative logs.
- Later replace direct stat loss with condition/recovery systems.

### Risk 4: Scope creep

Mitigation:

- Keep MVP limited to accounts, stats, logs, XP, levels, and admin configuration.
- Move achievements, quests, AI, social, and calories to later phases.

### Risk 5: Users do not return

Mitigation:

- First validate whether the core loop is satisfying.
- Later add streaks, quests, achievements, summaries, and social systems.

---

## 18. Future Roadmap

### Version 1.1

- Simple onboarding.
- Better level-up feedback.
- More log categories.
- Activity history improvements.

### Version 1.2

- Achievements.
- Streaks.
- Daily tasks.
- Weekly summaries.

### Version 2.0

- Quests.
- Daily ranks.
- Comeback quests.
- Character titles.
- Build types.

### Version 3.0

- Friends.
- Leaderboards.
- Multiplayer systems.
- Social comparison.

### Version 4.0

- Calories.
- Deficit, maintenance, surplus tracking.
- Macro tracking.
- Fitness-related streak bonuses.

### Version 5.0

- AI coach.
- Personalized quests.
- Behavior insights.
- Adaptive recovery mode.

---

## 19. Open Questions

- What are the first 20 predefined logs?
- What is the first XP-to-level formula?
- How exactly should global level be calculated?
- Should negative XP be able to reduce levels in the MVP?
- What does the admin panel need in the first version?
- What is the exact visual style reference?
- Should users be able to edit or delete logs?
- Should logs require time/date selection?
- Should the app show daily progress in MVP or only total progress?

---

## 20. Success Metrics

### MVP Success

The MVP succeeds if:

- The app works reliably.
- Users understand the concept quickly.
- Users enjoy seeing stats increase.
- Users manually log actions without feeling annoyed.
- Initial users return after the first few days.

### Future Metrics

- D7 retention.
- Number of logs per user per day.
- Average session length.
- Streak continuation.
- Achievement completion.
- Friend invites.
- Revenue.
- Active users.

---

## 21. Summary

This product should start as a simple real-life RPG dashboard where users log actions and see their character stats grow.

The MVP should avoid overcomplication and focus on proving the core emotional loop:

> I did something in real life → my character became stronger.

The long-term vision is to evolve into a social RPG and self-improvement super app focused on identity, lifestyle progression, and personal evolution.
