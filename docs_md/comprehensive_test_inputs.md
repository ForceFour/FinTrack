# Comprehensive Test Inputs for FinTrack Transaction Processing

## Test Case 1: Basic Mixed Transactions
"Bought groceries for $120 at Walmart yesterday and got paid $2500 salary this month"

**Expected Results:**
- Expense: -$120.00 (groceries category, Walmart merchant, yesterday's date)
- Income: +$2500.00 (salary category, employer merchant, today's date)

## Test Case 2: Multiple Expenses with Categories
"Spent $45 on coffee at Starbucks, bought clothes for $180 at Zara, and paid $75 for Netflix subscription"

**Expected Results:**
- Expense: -$45.00 (food_dining category, Starbucks merchant)
- Expense: -$180.00 (shopping category, Zara merchant)
- Expense: -$75.00 (entertainment/utilities category, Netflix merchant)

## Test Case 3: Income with Different Sources
"Received freelance payment of $800 from client, got $300 tip at restaurant, and earned $150 from selling old books"

**Expected Results:**
- Income: +$800.00 (freelance/consulting category)
- Income: +$300.00 (tips category, restaurant merchant)
- Income: +$150.00 (miscellaneous/sales category)

## Test Case 4: Complex Date Handling
"Paid $200 electricity bill on 15th September, bought gas for $60 yesterday, and received rent income of $1200 last week"

**Expected Results:**
- Expense: -$200.00 (utilities category, electricity bill, 2025-09-15)
- Expense: -$60.00 (transportation category, gas, yesterday)
- Income: +$1200.00 (rental income category, last week)

## Test Case 5: Mixed Complex Transactions
"I spent $350 on dinner at Olive Garden on 20th September, got paid $3200 salary at work this month, bought books for $85 at Amazon, and received $200 cashback from credit card"

**Expected Results:**
- Expense: -$350.00 (food_dining category, Olive Garden merchant, 2025-09-20)
- Income: +$3200.00 (salary category, work/employer)
- Expense: -$85.00 (shopping/education category, Amazon merchant)
- Income: +$200.00 (cashback/rewards category)

## Test Case 6: Ambiguous Cases
"Paid $50 for parking, transferred $500 to savings, bought medicine for $25 at CVS, and got refund of $30 from store"

**Expected Results:**
- Expense: -$50.00 (transportation/parking category)
- Income: +$500.00 (transfer/savings category) - wait, this might be expense depending on context
- Expense: -$25.00 (healthcare category, CVS merchant)
- Income: +$30.00 (refund category)

## Test Case 7: Very Complex Mixed Input
"On 15th September I bought furniture for $450 at IKEA, paid $120 for internet bill, received $2800 salary from company, got $150 freelance work payment, spent $65 on lunch at Chipotle yesterday, and bought groceries for $95 at Whole Foods"

**Expected Results:**
- Expense: -$450.00 (shopping/home category, IKEA merchant, 2025-09-15)
- Expense: -$120.00 (utilities category, internet bill)
- Income: +$2800.00 (salary category, company)
- Income: +$150.00 (freelance category)
- Expense: -$65.00 (food_dining category, Chipotle merchant, yesterday)
- Expense: -$95.00 (groceries category, Whole Foods merchant)

## Test Case 8: Edge Cases
"Donated $100 to charity, paid $2000 mortgage, received $500 gift from mom, bought car insurance for $150, and got $75 interest from bank"

**Expected Results:**
- Expense: -$100.00 (charity/donations category)
- Expense: -$2000.00 (housing/mortgage category)
- Income: +$500.00 (gift category)
- Expense: -$150.00 (insurance category)
- Income: +$75.00 (interest category)
