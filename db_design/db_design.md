## User
- user_id(PK, Text, default uid)
- username(TEXT, not null)

## AuthIdentity
- auth_id(PK, Text, default uid)
- user_id(FK->User.user_id, not null)
- provider(ENUM : EMAIL, GOOGLE, GITHUB)
- email(Text, not null)
- password_hash(nullable)
- is_verified(boolean, default false)
- created_at(not null)
UNIQUE(provider, email)

## Task
- task_id(PK, Text)(default uid)
- uid(not null, FK->User.uid)
- task_name(not null, Text)
- task_description(Text, Optional)
- status(Enum: COMPLETION | PENDING | UNDUE | CANCELLED)(Default: PENDING)
- category(Text, default: None, Fix enum values)
- scheduled_at(Optional)
- due_at(Optional)
- created_at(not null)
- last_edited(not null)
- completed_at (Optional)

## Behavior
- behavior_id(PK, Text)(default uid)
- uid(not null, FK->User.uid)
- task_id(FK->Task.task_id)(nullable)
- behavior_name(not null, Text)
- behavior_description(Optional)(Text,nullable)
- category(Text)(default none)(Fix enum values)
- created_at(not null)
- last_edited(not null)
- occured_at(not null, timestamp)
- source(default user)(USER_LOGGED | TASK_CONFIRMED)

## Diet
- behavior_id(PK,  FK->Behavior.id)
- diet_name(not null, Text)
- diet_description(Optional)(Text,nullable)
- calories(Optional, nullable)
- created_at(not null)
- last_edited(not null)

## Expense
- behavior_id(PK,  FK->Behavior.id)
- expense_name(not null, Text)
- Amount(not null, Text)
- expense_description(Text, nullable)(Optional)
- created_at (not null)
- last_edited (not null)

## WorkOut
- behavior_id(PK,  FK->Behavior.id)
- workout_name(not null, Text)
- workout_description(Optional)(Text)
- created_at(not null)
- last_edited(not null)

## TechWork
- behavior_id(PK, FK->Behavior.id)
- techwork_name(not null, text)
- techwork_description(Text, nullable)(Optional)
- created_at(not null)
- last_edited(not null)
