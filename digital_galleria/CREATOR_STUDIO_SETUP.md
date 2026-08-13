# Digital Galleria Creator Studio Upgrade

## URLs
- Creator Studio: `/creator-studio/` (staff/superuser only)
- Django Admin: `/admin/`
- Legacy admin alias: `/django-admin/`

## First run
```powershell
python manage.py migrate
python manage.py runserver
```

## Natural-language chatbot
The chatbot now keeps a conversation per logged-in customer and injects that customer's real account/order context.
For broad, natural questions, set an OpenAI API key in the environment:

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
$env:OPENAI_MODEL="gpt-4o-mini"
python manage.py runserver
```

If no API key is configured, the site still works with a safe local fallback responder.

## Ordering flow
Checkout is login-protected. Guests who try to checkout are sent to the existing login page and then returned through Django's normal `next` flow.

## Password
Passwords are deliberately simple: 4–16 ASCII letters/numbers only. No symbols or complicated requirements.

## Templates
Customer-facing templates were left intact except for the chatbot's first greeting so a logged-in customer is greeted by their display name. Creator Studio has its own template and does not redesign the storefront.
