# Create
## POST /api/v1/behaviors/
- Intent: create an entry of a behavior in database
- Input: user_id(from request context), behavior_name, behavior_description(Optional), occured_at ,category(optional), source(optional, default: USER_LOGGED), category_specific_detail(if categroy is present)
- Output: return behavior_id and success message
- Error: Invalid input, Constraint violation, Internal failure
### Server Logic
1. Extract all data mentioned in input
    - If any required data is missing -> reject
2. behavior_name and behavior_description must be a string with at least 5 character
    - if not -> reject
3. if categroy is not there:
    - insert a new entry in Behavior table with these data and get behavior_id in return
    - If query fail -> ROLLBACK -> return error message: Internal Server Error
    - return behavior_id and success message after succesful transaction

4. if category is there:
    - if category not in ["Diet", "Expense", "WorkOut", "TechWork"] -> reject: Invalid category
    - if category_specific_detail not there -> reject
    - Begin database transaction
        - insert new row in Behavior table and get behavior_id in return
        - insert new row into category_specific_table with category_specific_data and behavior_id(from upper query)
    - COMMIT and END transaction.
    - return behavior_id and success message
    - If any step fail -> ROLLBACK -> return error message: Internal Server Error

# Read
## GET /api/v1/behaviors?date=YYYY-MM-DD
## GET /api/v1/behaviors/{behavior_id}
## GET /api/v1/behaviors?category={}&from=YYYY-MM-DD&to=YYYY-MM-DD
- Intent: return the data requested by the user
- Input: user_id(from request context), behavior_id(from api endpoint if applicable), date(from query paramter if applicable)
- Output: return the data with success message
- Error: Invalid input, Constraint violation, Internal failure
### Server Logic
1. extract and validate the fields which is required from the api endpoint and/or query parameter
2. write a query to get all the data requested by the user from the database (with user_id)
3. if query fails -> return error message: Internal Server Error
4. serialize the data and return it with success message

# Update
## PATCH /api/v1/behaviors/{behavior_id}
- Intent: update the behavior sent by the client
- Input: user_id(from request context), data which user want to change(example behavior_name, behavior_description, category specific detail ,etc.)
- Output: return behavior_id and success message
- Error: Invalid input, Constraint violation, Internal failure
### Server Logic
1. Extract and validate all data mentioned in input
2. if category-specific payload is not there:(WITH immutability condition)
    - update the Behavior record with the data & & user_id provided by user
    - If query fail -> ROLLBACK -> return error message: Internal Server Error
    - return behavior_id and success message after succesful transaction
3. if category is there:
    - category not in ["Diet", "Expense", "WorkOut", "TechWork"] -> reject: Invalid category
    - BEGIN database transaction (WITH immutability condition)
        - update the category specific record in corresponding category table with the data provided by the user
        - update the Behavior record in Behavior table with the data provided by user & & user_id
    - COMMIT and END transaction.
    - return behavior_id and success message
    - If any step fail -> ROLLBACK -> return error message: Internal Server Error

# Delete
## DELETE /api/v1/behaviors/{behavior_id}
- Intent: To delete the data requested by the client
- Input: user_id(from request context), behavior_id(from query parameter)
- Output: return user_id with success message
- Error: Invalid input, Internal failure
### Server Logic
1. extract user_id and behavior id
2. BEGIN database transaction
    - delete the category record using behaviour_id in corresponding table
    - delete the behavior record using behaviour_id & user_id in Behavior table
3. COMMIT and END transaction.
4. return behavior_id and success message
5. If any step fail -> ROLLBACK -> return error message: Internal Server Error