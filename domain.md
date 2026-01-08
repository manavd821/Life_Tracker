## User
### Definition
An individual who own tasks and behaviour in the system.
### Core Characteristics
- Every user is uniquely identified by uuid.
- The User is the root of all data related to him.

## Goal(Task)
### Definition
It represents the action user aims to do.
### Core Characteristics
- A Task must belong to exactly one user.
- A Task may have a category for planning purposes.
- A Task has atmost one category.
### Sources
USER_LOGGED : explicitly entered by use.
### Key Invarients
- Daily Tasks must be atomic. Long-term goals may be abstract.
- A Task must not be auto-created without user.
- It may have scheduled start and/or end timestamps.
- It is immutable after end time.

## Behavior(Activity)
### Definition
It shows the action what user actually did - a factual, time-bound event reflecting real world action or experience.
### Core Characteristics
- Must belong to exactly one user.
- It must represent something which actully occur.
- It may exist without a task.
- It can optionally reference to task.
- It may have a category. If a category is present, a corresponding specialized record must exist..
### Sources
- USER_LOGGED : explicitly entered by user.
- TASK_CONFIRMED : created only after user confirms that planned task actually occured.
### Key Invarients
- A Behavior must not be auto-created without user confirmation.
- A Behaviour must have timestamp or duration.
- A Behaviour is immutable after a defined grace period.
- Expense, Diet, Workout, and TechWork are specialized extensions of Behavior and cannot exist without an associated Behavior.

## Expense
### Definition
It is the number which represents the money user spent on something.
### Core Characteristics
- It must belong to exactly one Behavior.
- It belongs to behavior only.
- It is the money user spend to consume something, which means it's irreversible.
- It can have repetative values.
- It has an text attribute "reason" to audit the spending. 
### Sources
- USER_LOGGED : Explicitly entered by user.
### Key Invarients
- It must be a positive number.
- It belongs to behavior only.
- It must have a time stamp.
- It must not include lending money.
- Atrribute "reason" is inseparable with it.
- It is immutable after defined grace period.
- If Behavior.category = EXPENSE, then exactly one Expense row must exist


## Diet
### Definition
It represents a qualitative records of the meal consumed by the user.
### Core Characteristics
- It belongs to exactly one user.
- It is a qualitative property(default).
- It can contain quantitative numbers(Optional).
- It can be part of Goal.
### Sources
- USER_LOGGED : Explicitly entered by user.
- TASK_CONFIRM : Created only after user confirmation.
### Key Invarients
- Diet must need user confirmation if it is coming from Task.
- Immutable after define period of time.
- If Behavior.category = Diet, then exactly one Diet row must exist.

## WorkOut
### Definition
It records the exercise activity performed by the user.
### Core Characteristics
- It is qualitative property by default.
- User can record quantified numbers optionally.
- It can be part of Goal.
### Sources
- USER_LOGGED : Explicitly entered by user.
- TASK_CONFIRMED : Created only after user confirmation.
### Key Invarients
- Workkout must need user confirmation if it is coming from Task.
- Immutable after define period of time.
- If Behavior.category = WorkOut, then exactly one WorkOut row must exist

## TechWork
### Definition
It represents tasks performed by the user that are associated with professional, technical, or career-related work and learning.
### Core Characteristics
- It can belongs to both - Goal and Behavior.
- It is the qualitative record.
### Sources
- USER_LOGGED : Explicitly entered by user.
- TASK_CONFIRMED : Created only after user confirmation.
### Key Invarients
- TechWork must need user confirmation if it is coming from Task.
- Immutable after define period of time.
- If Behavior.category = TechWork, then exactly one TechWork row must exist
