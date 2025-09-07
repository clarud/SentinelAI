from gmail_tools import mark_as_scam

# Replace with valid email and message ID
user_email = "sentinelaiginger@gmail.com"
message_id = "19923485ad715358"

try:
    result = mark_as_scam(user_email, message_id)
    print("Test Result:", result)
except Exception as e:
    print("Error:", e)