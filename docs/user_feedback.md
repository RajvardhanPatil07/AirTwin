# Practical user feedback

Status: no external user study or stakeholder endorsement has been recorded in
this repository. This protocol is ready to use; it is not evidence of adoption.

## Session

Ask a campus facilities staff member, environmental researcher or other intended
user to try the prototype for 10–15 minutes. Explain the cached timestamp,
interpolated map, assumed interventions and WorldPop 2020 modeled PCMC population (or synthetic fallback) first. Obtain
permission before recording or publishing their words; omit personal details.

Give the participant these tasks without showing them the answers:

1. Identify a location with high concentration and explain how old the reading is.
2. Find its forecast and explain what the displayed band means.
3. Compare industrial controls with dust suppression at the applied cuts.
4. Explain why the leading central estimate may not be a reliable policy winner.
5. State one actual decision this tool could help them explore and what evidence
   they would require before acting.

Record completion, misunderstandings, assistance needed and specific requested
changes. Ask whether they would use the workflow again and why. This small study
tests usability and relevance; it cannot establish real environmental impact.

## Evidence record to fill after a real session

| Field | Required evidence |
| --- | --- |
| Session date / participant code | Actual date and anonymous code |
| Relevant role | Broad role, with permission |
| Prototype revision / mode | Git SHA, observed or synthetic mode, snapshot date |
| Task outcomes | Completed / assisted / failed, with the observed reason |
| Feedback | Consent-cleared quotation or clearly labeled paraphrase |
| Resulting change | Linked issue and implementation PR |
| Follow-up | Actual retest result, or explicitly pending |

Do not fill the table with sample participants, plausible quotes or estimated
success rates. Attach evidence only after the session has occurred.

## Ready-to-run Bhosari session (15 minutes)

Recruit one campus facilities staff member or environmental researcher. Use
the same Bhosari workflow as the [demo](demo.md). This is a formative usability
session; one participant cannot establish adoption or general usability rates.

| Time | Facilitator action |
| --- | --- |
| 0–2 min | Explain the purpose, ask permission to take anonymous notes, and disclose cached data and synthetic inputs. |
| 2–10 min | Give the five tasks above one at a time. Ask the person to think aloud. Do not explain controls unless they request assistance. |
| 10–13 min | Ask the decision and evidence questions below. |
| 13–15 min | Summarize the observed problems and ask whether the summary is accurate. |

Prepare the connected PCMC backend with traffic 20%, industry 30%, dust 30%.
Check that Bhosari is present and note the timestamp before starting. An absent
station or backend failure is an observed task obstacle, not a successful session.

Opening script: “We are testing the prototype, not you. Please tell us what you
think as you use it. You may stop at any time. May we take anonymous notes?
Readings can be cached; source shares, intervention response and population are
assumptions. This session does not ask you to make a policy or health decision.”

Closing questions:

1. What actual task in your role could this support, if any?
2. What would you need before trusting the comparison of industrial controls and dust suppression?
3. Which displayed information was confusing or unnecessary?
4. Would you use it again? Why or why not?
5. May we publish your anonymous feedback? Ask separately before quoting exact words.

Use the [blank session record](user_feedback_record.md). Record each task as
completed without help, completed with assistance, or failed, with an observed
reason. Check whether the participant can explain the snapshot age, distinguish
forecast from observation, distinguish assumption ranges from confidence, and
distinguish synthetic exposure weights from people protected.

Afterward, turn each observed misunderstanding into a specific issue. Implement
the relevant change and ask the participant to repeat the affected task. Record
the retest separately. A refusal, criticism or failed task remains valid evidence.

**Current status:** session materials ready; participant, session, feedback and
retest pending. No recruitment message has been sent and no external feedback
has been invented.
