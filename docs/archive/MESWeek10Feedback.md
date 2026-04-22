[Announcements](https://brightspace.uri.edu/d2l/lms/news/main.d2l?ou=351479) Feedback

# Feedback

Manbir Singh Sodhi posted on Apr 21, 2026 12:18 PM

Please review the feedback provided online on the prototype/draft MES system to support the completion of your projects. You can access the feedback on Brightspace.  Some general comments:

# **On AI use**

You all used AI, and that was the right move. The assignment called for it. The real question was whether you used it well, and the strongest submissions made that clear.

The students who got the most out of it started with real domain knowledge and then used AI to structure what they already understood. Eacuello came in with 25 work centers and 9 product families from wire and cable manufacturing before asking for help. Blum already understood shipbuilding constraints, welder certification, and classification rules, so things like the Crawford learning curve, Transportation LP, and ISA-88 hierarchy showed up as deliberate choices, not AI suggestions. Reinhart had key constraints and optimization logic defined before generating anything. That pattern is the one to keep: domain first, AI second.

***Add figures before Week 11!***

None of the submissions included an ERD or a data flow diagram, and with schemas this large, that is the most useful thing you can add. Draw two simple visuals: one that groups tables by MESA function with foreign key links, and another that shows what each algorithm reads, writes, and passes along. It does not need to be polished. Even a clear hand drawn image works. Giving the LLM something visual will reduce mistakes in Week 11.

***Specify your dashboard before you build the database.***

Everyone mentioned dashboards in F11, but no one defined what they actually show. That matters because your schema needs to support those outputs. Before you start building, decide on three views: what the operator at the constraint sees in real time, what the supervisor sees across the line, and what the end of shift report includes. A simple matplotlib chart or even terminal output is fine. The key is to know what you are building toward.

***Scheduling.***

Some of you went beyond what the course required, which is good to see. Germosen modeled changeover costs in a way that actually matters for a high mix line. Blum used CPM with proper precedence logic, which fits shipbuilding far better than basic dispatching rules. These are the kinds of choices that matter. If your system has changeovers or precedence constraints and your current approach ignores them, Week 12 is the time to fix that.

***The bigger opportunity: optimization.***

This is the main thing to carry forward. You all designed systems with rich data and constraints, but most stopped at implementing formulas instead of asking what those formulas should optimize.

A few examples. Lot genealogy is not just about tracing forward and backward. It can minimize how much you need to quarantine. Process control is not just about detecting signals. It is about tuning parameters to balance false alarms, missed signals, and cost. And in Blum’s case, the learning curve feeds into scheduling, but it could also be used to assign work in a way that accelerates improvement where it matters most.

As you move into Week 12, take each algorithm and ask one more question: can this be better with the data you now have?

You have sensor history, failure logs, genealogy, and labor data. Use them. The difference between a system that runs and one that actually improves operations comes down to that extra step.

AI helped you build the foundation quickly. Now you decide what to build on top of it.


Personal Feedback: 

Overall Feedback

Hi Luke.

Your problem is perhaps the most creative problem in the class and we can expand this over summer if you want to. However, my feedback is on your use of AI specifically.  Your situation is different from anyone else in the class, and it deserves a different kind of comment.

The system concept — an Expeditionary Automated Repair Cell operating in a Disconnected, Intermittent, and Limited environment, with IMU-based kinematic monitoring, TinyML autoencoder integrity checking, and cryptographic recipe verification — is entirely original. No AI produces this from a generic "design an MES" prompt. You clearly brought a specific operational vision to the document, and it shows throughout. The integration timeline ("A Day at the EARC") is the best narrative in the class. The adversarial anomaly at 09:10 cascading through F5 → F8 → F9 → F1 → F2 is genuinely compelling systems thinking.

The problem is what happened after you gave the AI your creative brief. The evidence suggests you handed it an interesting concept and then accepted much of what came back without critically reviewing it against the course requirements. The result is a document that is simultaneously the most original in class and the most incomplete against the rubric — a combination that happens when a student's concept runs ahead of their execution.

Three specific places where this shows:

The F4 document control algorithm replaced the required version-control workflow with cryptographic hash verification. The hash approach is intellectually interesting and genuinely relevant to your adversarial context — but it answers a different question than the rubric asked. An AI given your brief ("adversarial environment, G-code tampering") would naturally emphasize the security angle and downplay the version-control workflow. You needed to catch that and add both. The fix is straightforward: keep the hash verification as your security layer and add a standard revision-control table (document ID, revision number, effective serial range, approval status, change authority) as the baseline version-control layer beneath it.

The F8 Trust Decay equation (Γ(t+1) = α·Γ(t) + (1−α)·N₀) has no course citation. This is an exponential smoothing variant, which is mathematically related to EWMA — a concept from the course. The AI almost certainly generated this formula without connecting it to course content because you did not tell it to. A one-sentence note in your document — "Trust Decay uses the EWMA smoothing structure from Week 10 F8, adapted with a fail-safe threshold at Γ ≤ 0.30" — would have satisfied the rubric and made the intellectual connection visible.

The Week 12 roadmap names only four algorithms. The rubric requires four to six. The four you listed are the four that make your system distinctive: EDD dispatcher, genealogy resolver, autoencoder pipeline, OEE aggregator. The two you omitted — MTBF-based PM scheduling and the X̄-R SPC check — are the two most standard algorithms in the course, which means the AI may have deprioritized them because your brief emphasized the novel cyber-physical elements. You needed to catch that and add them.

The pattern across all three gaps is the same: the AI followed your vision faithfully but optimized for originality at the expense of coverage. Your job in a document like this is not just to have an interesting idea — it is to make sure the interesting idea sits inside a complete specification. Going forward, after any AI session, run through the rubric checklist yourself line by line. The AI will not do that for you.

Looking forward to your demo video and final document.
