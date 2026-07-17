# Offline Conversation: Experience Review and Design Exploration

## Purpose

This document asks a player-facing question:

> How can the offline character feel like a living, particular person when it
> cannot rely on a language model?

It is not an implementation plan. It deliberately begins with game design,
interactive drama, authored performance, and player perception. Technical
schemas and portability decisions should follow only after a promising
experience has been demonstrated.

The offline mode is not expected to rival a strong language model at broad
knowledge, freeform analysis, or endlessly flexible phrasing. It should still
be able to hold a basic conversation, express a recognizable personality,
remember relevant experiences, continue its own life, misunderstand
gracefully, and preserve unfinished subjects for a future high-capability
session.

The standard is not "Did the engine return a valid response?"

The standard is "Did the player feel that somebody was there?"

## Current Offline Experience

The current offline turn is assembled from several bounded systems:

```text
player input
-> bounded input act
-> per-actor conversation continuity
-> contextual memory and open-loop retrieval
-> optional behavioral or initiative proposal
-> situated synthesis
-> canonical ActionDecision
-> conversation choreography
-> multimodal PerformancePlan
-> cartridge-authored offline realization
```

In ordinary language, the character currently:

1. Classifies the input as a greeting, statement, question, request, memory
   question, departure, return, correction, or similar broad act.
2. Tracks one active topic, two background topics, and one conversational
   obligation such as answer, clarify, acknowledge, repair, or follow up.
3. Searches for a relevant autobiographical memory, open loop, current
   activity, relationship expectation, or recent world change.
4. May propose one optional move such as probing, comparing, reminiscing,
   speculating, expressing curiosity, or continuing work.
5. Lets situated synthesis decide what survives alongside pressure, identity,
   intention, habit, self-monitoring, and current activity.
6. Selects one canonical action: speech, gesture, observation, continued
   activity, delay, silence, world action, or withdrawal.
7. Varies rhetorical strategy, conversational energy, pacing, response length,
   memory role, and activity relation.
8. Realizes the result with a small bank of cartridge-authored components.
9. When the topic exceeds offline capability, may retain it as unfinished
   business for a later model-enabled conversation.

This is much more than a keyword chatbot. It preserves causality, identity,
private state, world authority, and continuity. It can also complete a
nonverbal turn with no model call and without pretending that silence means the
character did not notice the player.

## What Is Already Working

The offline design has several important strengths.

### The character remains the same organism

Offline and online modes share identity, memories, relationships, activities,
pressures, intentions, actions, and consequences. Connecting a model changes
the available language realization, not the owner of the character.

### Unsupported knowledge is not invented

The system can defer, ask for clarification, retain a topic, or remain silent.
It does not need to hallucinate expertise merely to keep text moving.

### Memory and notes have real boundaries

Reminiscence must be grounded in an admitted autobiographical memory. Pending
topics are not silently treated as answered. The journal is an inventory tool
and subjective artifact, not a magical source of objective truth.

### Nonverbal behavior is first-class

Gesture, delay, continued activity, withdrawal, and silence are legitimate
outcomes. This is necessary for a character rather than a compulsory answering
machine.

### Character voices are separate from the engine

Pretorius and Kiki can have materially different realization material without
putting either character into core code.

These are valuable foundations. The problem is not that offline conversation
has no architecture. The problem is that the player does not consistently feel
the value of that architecture.

## Where The Illusion Breaks

### 1. Correct behavior can still feel empty

A turn can be perfectly valid while providing no rewarding interaction. A
silence caused by pressure, a silence caused by depleted initiative, and a
silence caused by missing conversational material are mechanically different,
but they may look identical to the player.

Expressive silence has dramatic meaning. Empty silence feels like a failed
chatbot.

### 2. The system tracks topics, but not enough shared meaning

"Henry Frankenstein" is a topic. It does not say whether the participants are:

- disputing Henry's motives;
- asking what happened;
- deciding whether to trust him;
- comparing Henry with the player;
- testing whether Pretorius feels remorse;
- avoiding the laboratory explosion;
- correcting an earlier claim.

Humans do not merely remain on a subject. They build, contest, repair, and
sometimes refuse a shared understanding of that subject.

The current obligation record helps, but it is too small to represent what has
actually been established, challenged, left ambiguous, or deliberately evaded.

### 3. Conversation is planned one turn at a time

Choreography creates variation inside a turn. It does not yet give a sequence
of turns a recognizable local shape.

A conversation might naturally move through:

```text
hesitant acknowledgment
-> narrow answer
-> revealing anecdote
-> disagreement
-> withdrawal
-> later return
```

Today, each turn can be locally sensible while the exchange as a whole feels
flat. The character varies delivery but does not always appear to be conducting
a scene.

### 4. Memories exist, but many are not conversationally tellable

A memory record is not automatically an anecdote.

To tell a memory naturally, a person usually selects:

- why it matters now;
- which concrete detail to mention;
- what can remain implicit;
- how certain the recollection feels;
- what emotional residue remains;
- what the listener is allowed to know;
- whether the memory supports, contradicts, or merely colors the current point.

The current system can retrieve a record and its present meaning, but offline
realization has little connective tissue for turning that material into a
small story.

This helps explain a recent crossplay result. The two characters had memory
stores containing roughly 180 and 201 records, yet the retrieved candidate sets
contained no eligible autobiographical episodes for initiative. The system was
not forgetting records. It lacked suitable lived material for that particular
exchange.

### 5. Repetition is now behavioral and functional, not merely textual

Recent work removed many exact and full-trajectory repeats. The corrected
30-day crossplay produced zero exact repeats, but semantic-move and trajectory
repeat rates remained about 47 percent.

That means the system can vary wording and pacing while repeatedly performing
the same kind of exchange.

The steady-collaborator test also exposed bounded pool exhaustion. Pretorius
repeated four clarification realizations because the same
`clarify|none|speak` situation recurred more often than the small authored pool
could support. Adding synonyms would delay the symptom without changing the
conversation.

### 6. Initiative has motives but too little socially usable material

The character can have a reason to speak without having a good conversational
move to make. In empty crossplay, 27 initiative proposals, mostly intrinsic
activity proposals, cleared their own source logic and then lost in synthesis.

This may be correct. A character should not blurt out every internal state. But
it also suggests a missing translation between:

```text
I care about this activity
```

and:

```text
There is now a socially appropriate reason to mention, demonstrate, invite,
compare, complain about, or continue this activity.
```

### 7. Shallow understanding produces repeated clarification

When the system cannot map a freeform utterance into something specific enough,
clarification is honest. Repeated clarification is not conversationally rich.

A person who only partially understands may also:

- respond to the emotional intent;
- reject the premise;
- answer the most likely interpretation with a qualification;
- identify the ambiguous word;
- offer two possible readings;
- defer the question;
- connect it to an adjacent known experience;
- decide the speaker is being intentionally vague;
- become impatient and move on.

The current offline repertoire uses only a portion of that space.

### 8. Offline mode reveals its content boundaries too easily

Once a player hears a clarification line or response shape several times, the
character begins to look like a fixture behind a counter. The player starts
probing the system rather than engaging the person.

This is not solved by a giant response database. It is solved by making a
smaller amount of authored material respond to meaningful differences in
scene, relationship, activity, memory, and conversational history.

### 9. The unrestricted text box promises more than offline mode can parse

Free text implies broad understanding. When the offline system repeatedly
narrows, deflects, or notes questions, the interface promise and actual
affordance diverge.

The answer is not necessarily to remove free text. The experience may need
subtle in-character affordances that help the player discover what can be
meaningfully discussed without exposing a command list or diagnostic error.

## Lessons From Game Dialogue

### Facade: beats, mix-ins, and graceful partial understanding

Facade separated surface text interpretation from context-specific character
reaction. It organized thousands of joint dialogue behaviors into dramatic
beats and allowed player reactions to mix into an ongoing performance. Its
authors reported natural-language understanding failures around 30 percent,
yet deliberately preferred extracting some plausible meaning over repeatedly
responding with a generic failure. The important lesson is not to copy its
authoring scale. It is to make misunderstanding part of the performance and to
resume the interrupted dramatic business afterward.

Sources:

- [Structuring Content in the Facade Interactive Drama Architecture](https://ojs.aaai.org/index.php/AIIDE/article/view/18722)
- [Natural Language Understanding in Facade](https://eis.ucsc.edu/papers/MateasSternTIDSE04.pdf)

### Versu: conversation as a social practice

Versu represented social practices as role-agnostic collections of affordances.
A greeting, meal, introduction, disagreement, or courtship scene establishes
roles, available actions, and local norms. Participants may follow or violate
those norms, and violations create new affordances such as disapproval,
forgiveness, anger, or departure.

This is highly relevant to Persona Engine. "Conversation" may be too broad a
context. "Interrupting exacting work," "returning to an unfinished inquiry,"
"receiving a correction," "attempting repair," and "being asked about a painful
memory" are different social practices even when they use the same text box.

Source:

- [Versu: A Simulationist Storytelling System](https://www.cs.engr.uky.edu/~sgware/reading/papers/evans2014versu.pdf)

### Comme il Faut: reusable social exchanges

Comme il Faut modeled social exchanges whose function is to change social
state, then retargeted them across characters and contexts. The authored unit
was not merely a sentence. It was a social act whose performance changed with
personality, relationship, cultural rules, and current concerns.

Persona Engine already owns many of those inputs. A small reusable layer of
social exchanges could make them observable without becoming a complete theory
of mind.

Source:

- [Social Story Worlds With Comme il Faut](https://www.cs.uky.edu/~sgware/reading/papers/mccoy2014cif.pdf)

### Quality-based narrative: small authored islands in systemic state

Failbetter's quality-based narrative uses small storylets whose availability
depends on changing state and whose outcomes change that state. Its practical
advice is especially important here: use a small number of broadly useful
qualities, avoid combinatorial character-specific branches, and let players
imagine the dark space between authored "fires."

Offline conversation does not need to author every sentence a person could
say. It may need a modest collection of high-value conversational storylets
that become available for clear reasons and leave durable consequences.

Sources:

- [StoryNexus Developer Diary: Quality-Based Narrative](https://www.failbettergames.com/news/storynexus-developer-diary-2-fewer-spreadsheets-less-swearing)
- [Narrative Snippets: Parsimony](https://www.failbettergames.com/news/narrative-snippets-parsimony-2)

### Context-aware game dialogue: select from facts, not merely topics

Naughty Dog's context-aware dialogue work described selection using individual
knowledge, collective knowledge, global game state, and the surrounding
environment. Valve's dynamic dialogue work similarly treated spoken material
as conditioned game content rather than a generic response to the last line.

Persona Engine already has richer state than many bark systems. The useful
lesson is that authored dialogue should be indexed by playable facts:

```text
who knows this
who witnessed this
what just changed
what activity is happening
what has already been said
what remains unresolved
who is present
what would be socially inappropriate now
```

Sources:

- [A Context-Aware Character Dialog System](https://www.gdcvault.com/play/1020386/A-Context-Aware-Character-Dialog)
- [AI-Driven Dynamic Dialog](https://media.gdcvault.com/gdc2012/slides/Programming%20Track/Ruskin_Elan_DynamicDialog.pdf)

## A Different Design Direction

The most promising direction is not a larger response pool. It is a small
conversation-play layer built from three ideas.

### 1. Temporary social practices

At any moment, the participants are not merely "chatting." They are engaged in
one local practice:

- greeting while occupied;
- interrupting work;
- asking for instruction;
- disputing a claim;
- recalling a shared event;
- disclosing a private memory;
- correcting an error;
- testing a boundary;
- attempting repair;
- resuming unfinished business;
- sharing an observation;
- ending an exchange.

The practice supplies roles, expectations, appropriate moves, violations, and
ways to end. It does not select the character's action. It defines the playable
social space in which existing cognition acts.

This is smaller than SocialMind and more immediately visible.

### 2. A shared-conversation ledger

Alongside the topic blackboard, the exchange needs a tiny record of shared
meaning:

- the question currently being answered;
- the proposition currently under discussion;
- whether it was asserted, accepted, doubted, corrected, or refused;
- the point of disagreement;
- what evidence was requested;
- what answer was only partial;
- what the character intentionally avoided;
- what should be resumed later.

This would distinguish "still discussing Henry" from "still deciding whether
Henry knowingly abandoned the work."

It should remain small. The purpose is not transcript storage. The purpose is
to let the next move build on what the exchange has accomplished.

### 3. Tellable memory material

Autobiographical records should remain untouched. Offline conversation can
derive a separate, bounded performance affordance from them: an anecdote card.

An anecdote card might contain:

- event identity;
- one concrete remembered detail;
- encoding-time interpretation;
- current interpretation;
- emotional residue;
- current relevance;
- disclosure boundary;
- possible social functions: explain, warn, compare, confess, boast, teach,
  challenge, or repair;
- whether this listener has heard it before;
- whether a shorter callback is now preferable to a full telling.

This does not create new memory. It makes existing memory playable.

## Other Approaches Worth Prototyping

### Micro-beat stacks

Instead of planning only the current turn, allow an exchange to hold a short
three-to-five-beat possibility:

```text
orient
-> develop
-> complicate
-> resolve or suspend
```

The beats are optional and interruptible. They do not force a plot. They give
the character a local sense of continuation.

### Character-shaped misunderstanding

Create fallback families based on what the character believes happened:

- partial answer;
- premise challenge;
- ambiguity fork;
- emotional acknowledgment;
- adjacent known subject;
- suspicious interpretation;
- impatience;
- deliberate deflection;
- silent acknowledgment;
- return to prior business.

Pretorius should not fail to understand in the same way Kiki does. The
difference should come from cartridge-authored priorities and performance,
not character names in engine code.

### Conversational affordance signals

Offline mode could expose subtle, optional cues:

- a visible unfinished topic;
- an object the character is currently handling;
- a remembered name that became salient;
- a brief activity callback;
- two in-character interpretations of an ambiguous question.

These are not menu commands. They help the player understand what the scene
currently affords, much as a game environment makes usable objects visible.

### Designed silence

Silence should carry a readable function:

- thinking;
- refusing;
- waiting for precision;
- returning to work;
- absorbing a correction;
- expecting the other person to continue;
- ending the subject.

If the player cannot infer which kind of silence occurred, the performance
needs one small observable cue.

### Conversational reservoirs

Each active practice could have a small reservoir of unused material:

- one fact;
- one memory;
- one opinion;
- one question;
- one activity observation;
- one relationship callback.

The character need not spend all of it. The reservoir simply distinguishes
"choosing not to extend" from "having nothing available."

### Listener-specific retellings

The same memory should not be told identically to Jay, Kiki, Henry, and a
stranger. The event remains the same, but the social function, detail, and
disclosure can differ.

This could make the existing actor registry and relationship state immediately
visible without requiring recursive mind-reading.

### Offline-to-online dramatic handoff

When offline capability is insufficient, the character can privately preserve:

- the exact unresolved proposition;
- why it mattered;
- what was already attempted;
- what evidence or knowledge was missing;
- the character's willingness to return to it.

When a model reconnects, the topic should reappear as unfinished personal
business, not as a system notification. The online renderer receives the same
character state plus a well-formed conversational situation.

## What Not To Do

### Do not attempt offline general intelligence

Offline mode should not imitate a frontier model badly. It should be excellent
at a bounded form of social and autobiographical play.

### Do not build a giant flat line database

More lines can postpone repetition, but flat content does not create
continuation, consequence, or motive.

### Do not use random synonyms as the main variation strategy

Variation should come from different situations, meanings, social functions,
memories, activities, and relationship states.

### Do not add another unconstrained executive

A scene practice, beat stack, or storylet selector should supply affordances
and context. Existing synthesis and `ActionDecision` must continue to own what
the character does.

### Do not let a drama system falsify the organism

No scene manager should force a confession, reconciliation, joke, or disclosure
merely because it would be dramatically convenient.

### Do not fill every silence

A living character does not need to be continuously entertaining. The goal is
legible choice, not maximum verbal output.

## Alternate Experience Frames

The current product frame is a familiar chat window. That is useful for
comparison with character-chat platforms, but it also creates the expectation
that every subject is equally available and that every turn should receive a
linguistically complete response.

Offline mode may feel more capable if its real strengths are perceptible in the
experience rather than hidden behind an unrestricted text box.

These are alternatives to explore, not recommendations to replace chat.

### The inhabited room

Conversation occurs around visible character activity. The player can see what
the character is handling, reading, repairing, or ignoring. Objects and changes
in the room provide natural conversational material.

The character no longer has to invent a topic merely to appear alive. The
world supplies shared attention.

### Episodic visits

Instead of implying an endless chat session, offline interaction can be framed
as visits with beginnings, interruptions, resumptions, and endings.

Between visits the character's activity, open loops, journal, and memory
continue. Returning after an absence becomes a meaningful scene rather than a
new chat window with retained context.

### Object-mediated conversation

The player can present a letter, photograph, laboratory object, journal page,
or prior message. The artifact creates a bounded shared subject and supplies
evidence that both parties can inspect.

This resembles classic adventure-game conversation: talking is grounded in
what the player and NPC are doing with the world.

### Asynchronous correspondence

Some offline exchanges could take the form of notes, letters, or messages that
do not demand an immediate full answer. The character may respond later, leave
part of the subject unresolved, or annotate it privately.

This frame naturally accommodates limited capability, delayed reflection, and
model reconnection without making them look like technical failure.

### Optional conversational affordances

Free text can remain primary while the interface quietly exposes a few current
possibilities:

- ask about the visible activity;
- return to an unfinished subject;
- challenge the current claim;
- present evidence;
- ask about a salient person or memory;
- leave the character to continue working.

These are not dialogue-tree answers written for the player. They are readable
affordances generated from existing state. They teach the player what kind of
social play the current scene supports.

### A conversation game rather than a chat service

The most radical alternative is to stop measuring offline mode against a blank
general-purpose chatbot. The player would still type naturally, but the
experience would openly revolve around:

- discovering what matters to the character;
- learning how this particular person handles interruption and disagreement;
- earning access to memories and disclosures;
- repairing misunderstandings;
- developing rituals;
- returning to long-running shared work;
- noticing how past interaction changes present conduct.

That is a narrower promise than universal chat and a much richer game.

## An Ideal Offline Scenario

The following is not a required script. It describes the quality of experience
we want.

### Situation

Pretorius is cataloguing a damaged apparatus. Jay arrives after several days
away and asks, "Did Henry ever understand what you were trying to make?"

### Desired experience

Pretorius recognizes a memory question and the social practice of discussing a
former collaborator while occupied.

He does not deliver a generic biography. He briefly continues sorting the
apparatus, then answers the most important part:

> "Understand? Intermittently. He understood the method whenever fear was not
> occupying the same chair."

The character has not invented a fact. The line realizes an existing
relationship interpretation and a tellable memory function.

Jay asks what that means. Pretorius selects one concrete recollection, not the
entire history:

> "At Ingolstadt he could follow an argument past every respectable boundary.
> Later, he began calling the boundary conscience."

The exchange now has shared conversational state:

```text
question:
    whether Henry understood the work
current answer:
    intellectually yes, emotionally inconsistently
point needing support:
    when Pretorius observed the change
character stance:
    proud, resentful, not ready to confess responsibility
```

Jay challenges the interpretation. Pretorius does not repeat the anecdote or
ask a generic clarification question. He may reject the premise, narrow the
claim, become irritated, or admit uncertainty depending on current
self-monitoring and evidence.

An interruption occurs. Pretorius returns to the apparatus without resolving
the disagreement. Two days later, when Jay mentions abandoned work, the prior
proposition becomes relevant and Pretorius may resume it in one sentence.

If Jay asks for a modern technical analysis that offline mode cannot support,
Pretorius does not suddenly become vague and helpful. He may say that the
question requires evidence he does not currently possess, privately retain the
unresolved proposition, and continue cataloguing. When a model becomes
available, he can return to the exact issue with the prior disagreement intact.

### Kiki under the same situation

Kiki should use the same underlying capabilities but conduct a different social
scene. She may answer more quickly, expose uncertainty more readily, connect
the memory to a familiar pre-2000 analogy, notice Jay's emotional intent, and
attempt repair sooner.

The engine remains shared. The playable social style is character-authored.

## Suggested Design Experiments

These experiments should be judged by human experience before becoming major
architecture.

### Experiment A: Four social practices

Author only:

1. interruption while occupied;
2. autobiographical question;
3. correction and disagreement;
4. return to unfinished business.

Give each practice a few roles, norms, violations, possible moves, and endings.
Run Pretorius and Kiki through the same situations.

Question:

> Does the player feel a coherent scene rather than a sequence of replies?

### Experiment B: Twelve tellable memories

Choose twelve existing Pretorius memories. Give each a bounded anecdote card
with a concrete detail, current meaning, possible social functions, and
listener-sensitive disclosure.

Ask about those subjects repeatedly across several days.

Question:

> Does memory begin to feel lived rather than retrieved?

### Experiment C: Fifty misunderstanding turns

Create inputs that are vague, compound, misspelled, metaphorical, emotionally
clear but factually unclear, or outside offline knowledge.

Evaluate whether the character:

- preserves immersion;
- varies repair strategy;
- responds to partial meaning;
- avoids false claims;
- avoids repeated clarification;
- returns to interrupted business.

Question:

> Can misunderstanding reveal character instead of revealing software?

### Experiment D: Offline-to-online continuity

Begin five difficult topics offline. Let the character answer what it can and
retain the actual unresolved propositions. Reconnect a model later.

Question:

> Does the renewed conversation feel like the same person returning to
unfinished thought?

### Experiment E: Blind scene review

Give evaluators transcripts without system labels and ask:

- What social situation were these people in?
- What did they disagree about?
- What changed during the exchange?
- What did the character avoid?
- Did the character seem occupied?
- Did the memory feel personally lived?
- Could you tell Pretorius from Kiki without signature catchphrases?
- Did any silence feel intentional?
- Would you continue the conversation?

These questions are more useful than response-validity alone.

## Ideal Success Criteria

Offline conversation is successful when:

- the player can maintain a basic exchange without feeling trapped in an error
  loop;
- familiar subjects become deeper over time rather than merely more repeated;
- the character can answer, partially answer, challenge, misunderstand,
  deflect, repair, wait, and leave in recognizable ways;
- memories enter because they serve the current social situation;
- the character appears to have an activity and interests independent of the
  player;
- silence has an inferable purpose;
- repeated questions acknowledge prior discussion;
- relationship history changes what is told and how;
- unsupported analysis becomes meaningful unfinished business;
- reconnecting a model expands expression without replacing the person;
- Pretorius and Kiki remain recognizably different even when the exact same
  social practice is active;
- a player remembers conversational moments, not merely system features.

## Open Design Questions

These questions should remain open during early prototyping:

1. Is offline mode primarily a permanent low-hardware experience, a temporary
   fallback, or both?
2. Should unrestricted text remain the only visible input, or may the current
   scene expose optional conversational affordances?
3. How much authored history is required before a new character feels lived?
4. Which memories deserve full anecdote cards, and which should remain short
   recollections?
5. How often should the character misunderstand rather than select a plausible
   partial interpretation?
6. When is silence expressive enough by itself, and when does it need a visible
   action?
7. Should social practices belong to the character cartridge, the world, the
   relationship, or a reusable content library?
8. How should a character revisit a known anecdote without repeating it or
   falsely changing the event?
9. What should the player be able to accomplish socially offline, beyond
   exchanging information?
10. How much difference between offline and online expression feels like
    expanded capability, and how much feels like a different person?

## Recommended First Exploration

Before designing another major subsystem, run a paper prototype.

Choose four social practices and twelve existing memories. Write each practice
on an index card with:

- roles;
- current social purpose;
- expected conduct;
- possible violations;
- a few available social moves;
- possible endings.

Write each memory on a second card with:

- one concrete detail;
- original meaning;
- current meaning;
- emotional residue;
- possible conversational functions;
- disclosure limits.

Then have one person play the engine and another play Jay, Pretorius, or Kiki.
The engine-player may use only the cards and the character's known state. Run
the same encounter several times with different energy, pressure,
relationships, and current activities.

This exercise can answer the most important question without writing code:

> Do social practices and tellable memories produce exchanges that feel more
> alive than turn-by-turn response selection?

If they do, the implementation boundary will be much easier to see. If they do
not, we can discard or revise the idea without adding another architectural
layer.

## Working Hypothesis

The offline character does not primarily need more intelligence.

It needs more playable conversational situations.

The existing organism can already remember, appraise, resist, choose, act,
learn, and remain silent. Offline conversation should become the game system
that stages those capacities into small social experiences:

```text
organism state
-> current social practice
-> shared conversational meaning
-> available storylets, memories, and repairs
-> synthesis-owned action
-> character-specific performance
-> visible consequence
```

That direction preserves the low-hardware and future C99 goals. More
importantly, it directs new work toward what the player can actually feel.

## Retro Topic-Family Pilot

The first implementation experiment deliberately chose a smaller approach
than a social-practice runtime. It keeps the existing organism and canonical
action pipeline, but gives the offline renderer a cartridge-authored topic
library.

The pilot contains four topics for Pretorius and four for Kiki. Each topic has:

- aliases and a small concept vocabulary;
- optional memory tags;
- first-mention, ordinary, expanded, uncertain, irritated, refusal, repeated,
  and relationship-sensitive response families;
- optional openings, memory callbacks, activity callbacks, and closings.

The engine also keeps a bounded, per-listener topic thread containing:

- discussion count;
- previous input function;
- recent semantic query signatures;
- recently used family and fragment identifiers;
- memories already disclosed through the offline topic track;
- last turn and last realization modality.

This state is shared across offline and model-backed conversation. Generated
model wording is not stored as authored dialogue, but discussing a topic
online still advances the same listener-specific thread. Returning offline
therefore does not reset the subject to a first introduction.

The topic library does not choose speech or action. It can only supply
realization material after `ActionDecision` has selected speech. Unknown or
partially recognized analytical questions still use the existing unresolved
note and later-capability handoff.

### Initial measurement

Two twelve-turn, single-topic trials were run:

```text
Pretorius: Henry Frankenstein and the work
12 turns
12 spoken turns
12 unique responses
0 silent turns
final topic-pool consumption: 41.4 percent

Kiki: identity and continuity
12 turns
12 spoken turns
12 unique responses
0 silent turns
final topic-pool consumption: 40.0 percent
```

The first Kiki trial used four high-frequency ordinary fragments and produced
only ten unique responses. Increasing that family to eight, while adding two
uncertainty realizations, removed the exact repeats in the identical trial.
This suggests an initial authoring heuristic:

```text
high-frequency ordinary family: 6 to 8 fragments
lower-frequency semantic families: 2 to 4 fragments
openings and closings: 2 each
total major-topic pool across all families: approximately 28 to 40 fragments
```

The 6-to-8 figure is not a total topic budget. Pool consumption counts every
fragment in every family, including openings, expansion, uncertainty,
irritation, refusal, repeated-question handling, relationship disclosure,
memory and activity callbacks, and closure. The pilot topics were not
over-authored ceiling tests; they are examples of the likely total budget for
a major recurring subject. Minor topics should use fewer families rather than
pretending that 8 to 12 fragments can support the same conversational range.

This is not yet evidence that the conversation feels alive. It only shows that
a modest corpus can survive a short sustained topic without immediate textual
pool exhaustion. Human testing must still judge:

- whether later turns deepen, resist, or close the topic naturally;
- whether the parser selects the right family rather than merely a different
  family;
- whether memories feel lived instead of inserted;
- whether relationship-sensitive material is earned;
- whether offline-to-online-to-offline continuity is perceptible;
- whether topic closure and silence occur before authored material becomes
  conspicuously mechanical.

The pilot also exposed and corrected two concrete grounding errors. A recent
transcript echo must not count as autobiographical memory support, and generic
engine activity labels such as `responding to interruption` must not appear in
authored activity callbacks.

### Harder continuity checks

Three additional checks were run before expanding the topic roster.

```text
Identical question five times:
5 spoken turns
5 unique responses
families: first_mention, expanded, repeated, repeated, repeated
final pool consumption below 50 percent

Return after three simulated days:
discussion depth retained
first-mention family not reused
recent fragment suppression retained

Offline -> model-backed -> offline:
one listener-topic thread used throughout
model-backed middle turn recorded as modality=ollama
offline return began at discussion depth 2
first-mention family not reused
```

These checks validate thread persistence and modality-neutral bookkeeping.
They do not establish that an online renderer will always express the intended
topic or proposition accurately. The model's wording remains noncanonical.

### Deliberate proposition-status limitation

The pilot does not yet represent proposition status.

It knows that the participants are discussing Henry, which response families
have been used, which semantic query shape recurred, and how deep or stale the
topic is. It does not maintain a shared record such as:

```text
claim: Henry understood the method
speaker stance: asserted
character stance: partly accepted
support: laboratory memory 12
challenge: fear changed Henry's later account
unresolved distinction: technical understanding versus moral acceptance
```

That omission is intentional for the pilot, but it remains a genuine gap.
Fragment variety solves pool exhaustion. Per-listener topic state solves
continuity and modality reset. Neither alone solves shared conversational
meaning.

The bounded active-claim ledger remains a deferred hypothesis, not the next
implementation step. It should be reconsidered only when a human visit
demonstrates a shared-meaning failure that cannot be corrected through authored
content, matching policy, listener history, or existing continuity state.
Fragment variety and topic continuity have passed the engineering proof; the
current work is a content-heavy experience proof.
