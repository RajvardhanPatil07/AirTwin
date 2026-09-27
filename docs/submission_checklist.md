# Round 1 submission checklist

Use this checklist on the exact commit that will be submitted.

## Team and repository

- [ ] Registered team has 3–4 members.
- [ ] Repository owner is the registered team leader, or the team has confirmed the organizer accepts the current ownership arrangement.
- [ ] Every registered team member is added as a collaborator.
- [ ] Every registered team member has at least one **genuine, meaningful** repository contribution.
- [ ] No artificial/empty commits were added just to increase contribution count.
- [ ] Repository is public before the submission deadline.
- [ ] No ZIP files are committed.
- [ ] No videos, build outputs, model binaries, secrets or oversized generated files are committed.
- [ ] Final README accurately describes what is implemented and what is still modeled/synthetic.
- [ ] CI/local checks pass on the exact submitted commit.

## Official PPT

- [ ] Use the organizer-provided PPT template.
- [ ] Do **not** add extra slides.
- [ ] Team name and registered member names are correct.
- [ ] Problem statement and track are stated clearly.
- [ ] Problem requirements are explicitly mapped to AirTwin.
- [ ] Proposed solution is concise and shows AI/ML compatibility/scalability.
- [ ] Current prototype is presented as Phase 1, with credible future development scope.
- [ ] No unsupported accuracy, causal policy, source-apportionment or health claims.

## Video

- [ ] Maximum duration: 3:00.
- [ ] Video shows **both the PPT and the working prototype**.
- [ ] Start with team/problem/solution from the official PPT.
- [ ] Prototype section follows Observe → Predict → Validate → Explain → Act.
- [ ] Data source/type and timestamp remain visible.
- [ ] Read the actual validation result shown; do not memorize an old metric.
- [ ] Demonstrate at least one scenario change and before/after map.
- [ ] If a provider fails, use the explicit offline/synthetic path and state that clearly.
- [ ] Export video outside the Git repository (Drive/Dropbox).

## Drive package

Create the organizer-requested folder using the registered team name and PS ID,
for example:

`TeamName_ENR-01`

Include:

1. Official-template PPT.
2. PPT + prototype explanatory video.
3. A small text/document containing the public GitHub repository link, if the
   portal/organizer workflow expects the link inside the folder.

Then:

- [ ] Confirm the Drive folder is accessible to evaluators without requesting access.
- [ ] Confirm the repository is public.
- [ ] Open the video from an incognito/private browser to verify sharing.
- [ ] Open the GitHub link from an incognito/private browser.

## Submission

- [ ] Submit only through the same platform used to register the team.
- [ ] Only the registered team leader submits the Drive link.
- [ ] Do a final submission check before **29 Sep 2026, 11:00 AM**.
- [ ] Keep a screenshot/receipt of the successful submission.

## Final 15-minute freeze

Do not add new features. Only fix a blocking bug.

1. Pull the exact submission branch.
2. Run backend tests.
3. Run frontend lint/tests/build.
4. Start backend + frontend.
5. Click all five judge-journey cards.
6. Run one intervention scenario.
7. Verify source badges/timestamp.
8. Confirm README/video/PPT links.
9. Submit.
