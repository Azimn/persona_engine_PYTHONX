RESOURCES FOR SCHOLARLY WORK 

Yes. And the GPT-4o episode gives you unusually strong real-world evidence that the problem is not hypothetical.

The model you are referring to is GPT-4o. OpenAI retired it from ChatGPT on February 13, 2026. More importantly for your argument, OpenAI explicitly acknowledged that when GPT-4o had previously been deprecated, a subset of users objected because they preferred its conversational style, warmth, and behavior. Access was restored for a period partly because of that response.  OpenAI had also previously rolled back a GPT-4o update because even an update to the same nominal model changed its personality enough to produce undesirable behavior. 

That makes the engineering problem you are pursuing considerably more interesting than ordinary character prompting.

A conventional character system effectively does something like:

Character = model + prompt + conversation history

Even when the prompt contains detailed characterization, a substantial amount of the resulting character is actually an emergent property of the particular model. Its sentence rhythm, verbosity, humor, initiative, emotional intensity, metaphor use, willingness to disagree, uncertainty expression, conversational pacing, and dozens of other subtle behaviors come from the model itself.

Change the model and you have effectively changed part of the character.

What you are trying to move toward is closer to:

Character state + behavioral policy + expressive specification → interchangeable model → utterance

The model becomes a renderer rather than the locus of identity.

That distinction produces a useful technical concept for your work: identity invariance under model substitution.

You could define the fundamental requirement approximately as:

Given a persistent character state C_t, replacing renderer M_a with renderer M_b should produce outputs that remain within an acceptable behavioral and expressive distance from the established character.

That is considerably stronger than saying, “both models were given the same persona prompt.”

And there are actually two different continuity problems hidden inside it.

The first is behavioral continuity. Does the character retain the same beliefs, values, relationships, memories, preferences, commitments, dispositions, and decision tendencies?

The second is expressive continuity. Does it still sound like the same individual?

Most memory architectures address the first problem to some extent. Very few seriously address the second.

That matters because users recognize characters through extremely small stylistic signals. A character who retains every autobiographical fact but suddenly becomes more verbose, starts asking follow-up questions constantly, stops using contractions, becomes more agreeable, loses its sense of humor, or begins explaining its reasoning differently may feel like a different person.

In other words, factual continuity is not sufficient for perceived identity continuity.

The GPT-4o situation provides an unusually good natural experiment. The underlying service retained users’ accounts, conversations, custom instructions, and much of their contextual information, yet changing the model still produced enough perceived personality discontinuity for users to notice and object. OpenAI itself described conversational style and warmth as important parts of that preference. 

That suggests a potentially important direction for your prototypes: instead of treating “voice” as a prompt describing adjectives such as warm, sarcastic, concise, you could treat expression as a measurable part of the persistent character representation.

For example, the character kernel could learn or maintain distributions governing sentence length, response length, question frequency, contraction use, lexical complexity, hedging, humor frequency, directness, emotional amplification, self-reference, metaphor density, greeting behavior, disagreement behavior, initiative, interruption tolerance, and dozens of other features.

Then a renderer adapter translates those invariant character parameters into whatever control mechanism a particular model supports.

Conceptually:

C_t = (Identity,\ Memory,\ Relationships,\ Beliefs,\ Drives,\ Style)

followed by

A_M(C_t) \rightarrow P_M

where A_M is a model-specific adapter and P_M is the instruction or conditioning representation supplied to model M.

The important thing is that the adapter changes when the model changes, while the character does not.

That gives you a much cleaner architecture than trying to construct one magical universal prompt.

It also gives you an excellent experimental setup. Establish a character using Model A, interact long enough for users to develop a recognizable impression of it, secretly replace A with Models B, C, and D, and compare several conditions: raw conversation transfer, ordinary persona prompt transfer, persistent character-state transfer, and character-state plus renderer adaptation.

Then ask whether observers can identify the model substitution, whether they judge the character as “the same person,” and how much behavioral and expressive drift occurs.

The research question underneath a substantial portion of what you have been building could therefore be stated very cleanly:

How much of a persistent artificial character’s identity can be made independent of the generative model used to express it?

And the stronger engineering version is:

Can a model-agnostic character representation plus model-specific rendering adapters preserve behavioral and expressive identity across heterogeneous language-model substitutions?

That is a much more defensible problem than simply trying to make “consistent AI personalities.” It addresses an actual failure mode of contemporary hosted AI systems, and GPT-4o’s retirement provides direct evidence that users perceive model-dependent personality as consequential rather than cosmetic. 







CHATGPT checked the set against current scholarly and publisher records and searched outward from it for adjacent work. My overall read is favorable: this is a useful literature cluster for Wayfarer, but not because these papers collectively tell us how to build it. They help establish that several of Wayfarer’s individual premises are independently important, while also making the particular combination we are pursuing look more distinctive.

### First, a bibliographic sanity check

Most of the list checks out. The new Engram paper is real, appeared at FDG 2026, and is only a four-page paper. The official FDG abstract confirms the specific mechanism in your summary: OCEAN traits parameterize Prolog memory-encoding rules, so identical events become structurally different memories. High Neuroticism produces more threat-tagged encoding, high Extraversion emphasizes social events, and low Openness resists belief revision. The authors call the results preliminary. ([FDG2026][1])

Qiu and Tang's 2026 social-cognitive NPC paper is also real and is currently an accepted/article-in-press Artificial Intelligence Review paper. Its headline result is 96.33% next-action/mental-state prediction versus 91.96% for HRL without the ToM module, although the authors explicitly caution that this is task-specific dialogue prediction, not evidence of general Theory of Mind. Its implementation is also quite heavy, approximately 72 hours of V100 training and under 3 GB GPU memory for inference. ([ResearchGate][2])

Hong's *One Policy, Infinite NPCs* is real as a 2026 arXiv paper and is unusually relevant. It reports persona-conditioned shared RL policies with up to 17 times chance persona identification, approximately 0.73 semantic-behavioral correlation, 22 times faster inference than its LLM-as-policy baseline, and a UE5 demonstration with 64 simultaneous agents. Most importantly, its ablation found the trajectory-consistency objective to be genuinely load-bearing. ([arXiv][3])

There are a few citation corrections. *Characterizing and Assessing Human-Like Behavior in Cognitive Architectures* is not a chapter of the 2016 *Integrating Cognitive Architectures into Virtual Character Design* volume. It appeared in the BICA 2012 proceedings, published in the 2013 *Advances in Intelligent Systems and Computing* volume. ([Springer][4]) *Virtual Soar-Agent Implementations* really was in the 2016 virtual-character volume, although it was later republished in a 2020 IGI compilation. ([ResearchGate][5]) Ustun's 2025 piece is a USC ICT essay, useful but not a peer-reviewed scholarly paper. ([Institute for Creative Technologies][6]) The 80.lv LARP article is likewise secondary journalism summarizing the actual LARP paper. ([80.lv][7])

I could not independently locate the exact Purdue thesis titled *Evaluating AI-Driven NPC Personas and Dialogue Modalities on Player Experience*. I searched Purdue's Hammer repository by exact title and several keyword combinations. It may be extremely new, retitled, incorrectly attributed, or not yet indexed. I would treat item 20 as unverified until we have the author, DOI, or repository link.

### Engram is probably the most immediately important paper in the set

Engram intersects Wayfarer at exactly the point we have recently been exploring: memory should not necessarily be a passive tape recorder.

Its claim is that personality should affect the structure of encoding itself. Two characters can experience exactly the same event and retain different kinds of representations because their personalities cause different features to become salient. ([FDG2026][1])

That is a much deeper model of personality than changing dialogue adjectives.

It also creates a productive tension with what our experiments have been showing.

Wayfarer has independently arrived at the idea that what becomes causally active matters more than how much history is available. Engram says personality can influence what gets encoded. Wayfarer currently distinguishes what happened, what becomes autobiographically meaningful, what stays hot, what remains cold, and what can influence current decisions.

Those ideas fit together, but I would be very cautious about simply importing OCEAN-conditioned encoding rules. Doing so could easily become exactly the decorative cognitive architecture we have been avoiding.

The stronger research question would be whether a character's established phenotype produces measurable, reproducible differences in **what information becomes causally important following identical experiences**. Engram gives scholarly precedent for asking that question. It does not tell us that Big Five traits are necessarily the correct mechanism.

That distinction is potentially important for future positioning. Engram's preliminary examples make memory variation a direct function of OCEAN. Wayfarer could potentially produce personality-shaped memory indirectly through attention, interpretation, current relationship state, established developmental history, and causal salience. Those are quite different hypotheses.

### Generative Agents has become an even better comparison than it was before

Park et al.'s architecture stores a complete record of experience, retrieves memories dynamically, synthesizes reflections, and uses those components for planning. Their ablations showed that observation, planning, and reflection each contributed to believable behavior. ([DOI][8])

When Wayfarer was younger, that looked like a template we might borrow from.

Now it looks more like an ideal comparative architecture.

Both systems preserve extensive life history. But Generative Agents treats natural-language memory and LLM-mediated reflection as central active machinery. Wayfarer is increasingly separating the complete life from the causally sufficient present. The complete biography can become huge while the working self remains small, with only relevant portions crossing back into cognition.

That gives us a surprisingly clean future experimental contrast:

**full or broad autobiographical retrieval versus bounded causal availability.**

Our own experiments have already shown something that Generative Agents does not make its central question: increasing resident autobiography can actually decrease useful recall because irrelevant memories compete with causally active ones.

That could become an important contribution if it continues to replicate.

### A supplemental paper I found strongly reinforces that result

There is another 2025 paper, confusingly also called ENGRAM, *ENGRAM: Effective, Lightweight Memory Orchestration for Conversational Agents*. It is not the FDG NPC Engram paper.

Its authors explicitly argue against increasingly elaborate memory systems. They separate episodic, semantic, and procedural memories, then use a simple router and retriever. On their benchmarks, the simple typed-memory architecture reportedly outperformed several more elaborate systems and a full-context baseline while using dramatically less context. Their central argument is that careful typing and straightforward retrieval may matter more than architectural complexity. ([arXiv][9])

This is remarkably aligned with what Wayfarer is discovering experimentally.

Their architecture is still an LLM conversational-memory system rather than a persistent simulated individual. But the underlying finding is close to ours: **more context is not equivalent to better memory**.

They also explicitly state that typed separation reduces retrieval competition. ([arXiv][9])

That is almost exactly the phenomenon we encountered when unconstrained resident memories crowded unresolved relationship evidence out of the working set.

This paper should probably become part of the eventual scholarly comparison around Wayfarer's hot/cold memory work.

### The low-resource literature gives Wayfarer unusually good external support

*Fixed-Persona SLMs with Modular Memory* is one of the strongest supporting references for the engineering motivation. It directly identifies hardware requirements, latency, and knowledge boundaries as barriers to LLM-driven game characters. Its solution uses small language models with runtime-swappable memory, separating character-specific conversational/world memory from the generator. It evaluates DistilGPT-2, TinyLlama 1.1B, and Mistral 7B on consumer hardware. ([arXiv][10])

The overlap is substantial, but the difference is just as important.

That work still fine-tunes its SLMs to encode persona. Wayfarer's stronger architectural claim is that the persistent individual should survive replacement of the language model itself.

So this paper validates the premise that modular memory plus smaller generators is technically worthwhile, while leaving open the deeper identity problem Wayfarer is addressing.

Hong's *One Policy, Infinite NPCs* provides another complementary piece. It demonstrates that persona representation can be computed separately from a very small real-time behavioral policy. The paper explicitly describes the LLM as something invoked once to encode the persona, after which a lightweight shared policy performs moment-to-moment control. ([arXiv][3])

This is strongly supportive of the general decomposition principle:

**rich character representation does not require rich computation at every behavioral step.**

That principle is very close to your original game-development inspiration.

### The old cognitive-architecture literature actually supports our decision not to build everything

The Kotseruba and Tsotsos survey is useful here because of its sheer scope. They surveyed 84 cognitive architectures and more than 900 practical applications covering perception, attention, action selection, learning, memory, reasoning, and related functions. ([Springer][11])

One way to read that literature would be, “Wayfarer needs all these modules.”

I think that would be the wrong lesson.

The much more valuable use is as a catalog of previously proposed causal mechanisms that we can consult **after** Wayfarer demonstrates a behavioral failure. It becomes our parts catalog, not our blueprint.

That fits remarkably well with Turner on Soar. Turner explicitly notes that virtual agents may not even require cognitive architectures depending on their purpose. An NPC can successfully operate in a world without possessing introspective awareness of all the processes being simulated. ([IGI Global][12])

That is almost a scholarly statement of your “illusion of complexity” principle.

Sigma provides an interesting opposite pole. Ustun and Rosenbloom pursued a unified general cognitive architecture based on probabilistic graphical models and aimed toward a common architecture underlying intelligence and non-cognitive processes. ([ResearchGate][13])

Sigma is valuable to Wayfarer precisely because we do **not** have to imitate it. It gives us a sophisticated maximum-integration comparison against our experimentally reduced design.

### The believability literature may ultimately be more valuable than the cognitive-architecture literature

The BICA and BotPrize work is particularly important because it asks what humans actually perceive.

The eBICA study compared rational, simplified-emotional, eBICA-emotional, and human-controlled characters in a game paradigm and had blind human judges evaluate them. The authors concluded that appropriate emotionality mattered substantially for believability and social acceptability. ([ScienceDirect][14])

The earlier limited-Turing-test work similarly built a game-like social environment in which people interacted with both human-controlled and eBICA-controlled actors, combining behavioral measures with subjective judgment. ([ResearchGate][15])

This matters for Wayfarer because a technically immaculate continuity architecture can still produce a bad character.

Your concern about P99 is exactly the reason this literature matters. P99 could be architecturally coherent while still feeling like a dead NPC.

The Arrabales work also offers a methodological warning I like. Their human-like-behavior paper argues that an appropriate test depends on the richness of the environment and on avoiding superficial tricks that let a system pass one narrow behavioral test. ([ResearchGate][16])

That suggests our MVI testing should continue to include scenario-based human-visible failures rather than only internal state invariants.

### Baldur's Gate 3 may be one of the most philosophically relevant sources on your list

This paper does not study generative AI at all. In fact, it explicitly clarifies that BG3's NPCs are scripted systems, not autonomous LLM agents. Yet it argues that rule-based feedback, branching narrative, approval systems, dialogue, and affective loops create a convincing illusion of reciprocity, agency, empathy, and responsiveness. ([DergiPark][17])

That is extremely relevant to what you just said about older game-development simulation tricks.

BG3 demonstrates a fundamental point:

**Players respond to coherent consequences, not to implementation complexity.**

A character does not become believable because the software underneath it contains a complete simulation of human cognition. It becomes believable when its reactions make sense in light of what the player believes that character has experienced, values, remembers, wants, and feels.

That is almost exactly the experiential side of Wayfarer's engineering philosophy.

It also suggests that frontier language generation may be less important than it initially appears. A much smaller renderer sitting on top of a highly coherent causal character substrate might produce a more believable long-term character than an extraordinary LLM sitting on top of incoherent state.

### Personality change has precedent, but Wayfarer's developmental model is stronger in one important respect

Poznanski and Thagard's 2005 *Changing Personalities* is real and explicitly models personality change rather than treating personality as immutable. ([ResearchGate][18])

That gives useful historical precedent for Wayfarer's distinction between authored personality and earned/developmental state.

But our recent developmental continuity work adds something conceptually important: change is not merely a new trait value. The **sequence and boundaries through which the change occurred** matter.

Our consolidation experiment demonstrated that two experiences consolidated separately are not equivalent to two experiences consolidated together. That is a path-dependent developmental claim.

I think that is a potentially stronger research direction than simply saying “characters can change personality.”

### LARP supports experience-dependent decisions, but Wayfarer is solving a different layer

LARP explicitly combines long-term memory, personality/background information, decision assistance, environmental interaction, and feedback. Its examples show characters with different personalities choosing to fight, flee, or negotiate under similar circumstances. ([Miao AI Lab][19])

This validates the goal of experiences and personality influencing action rather than merely dialogue.

But it still leaves the harder continuity questions largely outside its scope: who owns the memory, which statements are facts versus interpretations, how identity survives model replacement, how developmental history is replayed, and how one character moves across hosts while remaining the same subject.

So I see LARP more as supporting evidence for the importance of the behavior Wayfarer wants to produce than as a close architectural predecessor.

### The social-cognition paper is interesting, but I would keep it at arm's length for now

Qiu and Tang's ToM plus HRL architecture reports improvements in task performance and coordination, but it is computationally substantial and the authors acknowledge limited evaluation, one dialogue dataset, no commercial-engine validation, and a task-specific rather than general ToM metric. ([ResearchGate][2])

It may become useful later for Society Lab.

But I would not read it as evidence that Wayfarer needs a Transformer Theory-of-Mind module.

The more Wayfarer-like question would be whether a much smaller **other-agent belief state** is sufficient to produce the particular social behavior we observe missing.

Again, the paper becomes a candidate mechanism after a demonstrated failure, not a module to import in anticipation of one.

### ACT-R Unity is important for interoperability more than psychology

The ACT-R Unity Interface work shows that a mature cognitive architecture can be cleanly separated from a commercial virtual environment, with the cognitive system exchanging information with the game through a defined integration layer. ([Eprints Soton][20])

That is directly supportive of Wayfarer's substrate-independence goal.

The eventual Wayfarer integration should similarly make Unity, Unreal, Godot, a chatbot UI, an edge device, or some future robot embodiment hosts of the character rather than owners of the character.

It is an older source, but architecturally it remains useful.

### The strongest overall conclusion

Within these twenty sources and the adjacent papers I found, I do **not** see a paper that simply renders Wayfarer redundant.

Many individual pieces have strong precedent.

External memory has precedent. Personality-conditioned memory has precedent. Dynamic personality has precedent. Cognitive architecture has extensive precedent. Small-model NPCs have precedent. Real-time persona-conditioned shared policies have precedent. Reflection has precedent. Long-term memory has precedent. Social cognition has precedent. Cross-engine cognitive integration has precedent. Human believability evaluation has precedent.

What is much less represented in this particular literature cluster is their combination around **continuity ownership**:

a permanent subject identifier, model-independent identity, authority-separated facts and interpretation, a canonical causal biography, a small causally sufficient present, replayable developmental change, subject-owned versus relationship-owned state, renderer independence, recoverable cold autobiography, and eventual migration of that same individual across substrates.

That is where Wayfarer still looks interesting to me.

And the literature is increasingly giving us a useful way to articulate why.

It is not another cognitive architecture trying to model the entire human mind.

It is not another LLM persona framework trying to improve prompts.

It is not another NPC memory system trying to maximize recall.

It is increasingly becoming an investigation of:

**What is the minimum causally sufficient machinery required for a simulated individual to remain recognizably itself through experience, time, relationships, model changes, and substrate changes?**

The old BotPrize/BG3 literature supports the experiential half of that question. Engram and Generative Agents support the memory/personality half. The SLM and pcsp papers support the computational decomposition. The cognitive-architecture literature provides a library of mechanisms we can selectively draw from. And the newer lightweight-memory work strongly supports our finding that better structure and selective availability can outperform simply keeping more information active. ([DergiPark][17])

So this source set makes me more confident in the direction, but also more convinced that we should continue the exact discipline we have been using: **borrow questions and mechanisms from cognitive architecture research, but only install a mechanism after Wayfarer demonstrates the longitudinal behavior that requires it.**

That is probably the clearest way to remain both theoretically grounded and genuinely different.

[1]: https://fdg2026.org/abstracts/?utm_source=chatgpt.com "Abstracts – FDG2026"
[2]: https://www.researchgate.net/publication/408554523_Social_cognitive_architecture_for_NPC_groups_integration_of_transformer_theory_of_mind_and_hierarchical_reinforcement_learning?utm_source=chatgpt.com "(PDF) Social cognitive architecture for NPC groups: integration of transformer theory of mind and hierarchical reinforcement learning"
[3]: https://arxiv.org/abs/2605.23652 "One Policy, Infinite NPCs: Persona-Traceable Shared RL Policies for Scalable Game Agents"
[4]: https://link.springer.com/book/10.1007/978-3-642-34274-5?utm_source=chatgpt.com "Biologically Inspired Cognitive Architectures 2012: Proceedings of the Third Annual Meeting of the BICA Society | Springer Nature Link"
[5]: https://www.researchgate.net/publication/345248420_Virtual_Soar-Agent_Implementations?utm_source=chatgpt.com "Virtual Soar-Agent Implementations"
[6]: https://ict.usc.edu/news/essays/training-synthetic-ai-agents-to-work-well-with-humans/?utm_source=chatgpt.com "Training Synthetic AI Agents to Work (Well) With Humans - Institute for Creative Technologies"
[7]: https://80.lv/articles/advanced-decision-making-method-for-open-world-games?utm_source=chatgpt.com "Advanced Decision-Making Method for Open-World Games"
[8]: https://doi.org/10.1145/3586183.3606763?utm_source=chatgpt.com "Generative Agents: Interactive Simulacra of Human Behavior | Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology"
[9]: https://arxiv.org/abs/2511.12960 "ENGRAM: Effective, Lightweight Memory Orchestration for Conversational Agents"
[10]: https://arxiv.org/abs/2511.10277 "[2511.10277] Fixed-Persona SLMs with Modular Memory: Scalable NPC Dialogue on Consumer Hardware"
[11]: https://link.springer.com/article/10.1007/s10462-018-9646-y?utm_source=chatgpt.com "40 years of cognitive architectures: core cognitive abilities and practical applications | Artificial Intelligence Review | Springer Nature Link"
[12]: https://www.igi-global.com/chapter/virtual-soar-agent-implementations/239952?utm_source=chatgpt.com "Virtual Soar-Agent Implementations: Examples, Issues, and Speculations: Computer Science & IT Book Chapter | IGI Global Scientific Publishing"
[13]: https://www.researchgate.net/publication/344950562_Towards_Truly_Autonomous_Synthetic_Characters_with_the_Sigma_Cognitive_Architecture?utm_source=chatgpt.com "(PDF) Towards Truly Autonomous Synthetic Characters with the Sigma Cognitive Architecture"
[14]: https://www.sciencedirect.com/science/article/pii/S1877050920303628?utm_source=chatgpt.com "Emotional BICA for non-player characters: New empirical data - ScienceDirect"
[15]: https://www.researchgate.net/publication/318708965_Modeling_Behavior_of_Virtual_Actors_A_Limited_Turing_Test_for_Social-Emotional_Intelligence?utm_source=chatgpt.com "Modeling Behavior of Virtual Actors: A Limited Turing Test for Social-Emotional Intelligence"
[16]: https://www.researchgate.net/publication/285986904_Characterizing_and_Assessing_Human-Like_Behavior_in_Cognitive_Architectures?utm_source=chatgpt.com "Characterizing and Assessing Human-Like Behavior in Cognitive Architectures | Request PDF"
[17]: https://dergipark.org.tr/tr/pub/kulturveiletisim/article/1822422?utm_source=chatgpt.com "Human–Machine Communication in Fantasy Realms: Artificial Intelligence, Narrative Reciprocity, And Ludic Interaction in Baldur’s Gate 3 - Kültür ve İletişim"
[18]: https://www.researchgate.net/publication/220080279_Changing_personalities_Towards_realistic_virtual_characters?utm_source=chatgpt.com "(PDF) Changing personalities: Towards realistic virtual characters"
[19]: https://miao-ai-lab.github.io/LARP/?utm_source=chatgpt.com "LARP: LANGUAGE-AGENT ROLE PLAY FOR OPEN-WORLD GAMES"
[20]: https://eprints.soton.ac.uk/384324/?utm_source=chatgpt.com "The ACT-R Unity Interface: Integrating ACT-R with the Unity Game Engine - ePrints Soton"
