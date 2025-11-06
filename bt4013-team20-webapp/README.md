## Run App
First navigate to the app's directory:
```text
bt4013-team20-webapp/
├── myapp/   <-- navigate here!
│   └── ...
├── .gitignore
├── requirements.txt
└── README.md
```

Run the web app with the following command:

```bash
python manage.py runserver
```

Note:
- In templates/base.html, the login and logout URLs are temporarily set to "#" for testing purposes. Remember to change them back to `{% url 'accounts:login' %}` and `{% url 'accounts:logout' %}` respectively before deploying the application. (lines 138, 139, 141, 147, 191)
- Uncomment out the `@login_required` decorator in myapp/skillgraph/views.py (line 5) before deploying the application.
- Uncomment out other urls in myapp/urls.py that were commented out for testing purposes.
- Uncomment out other apps in myapp/settings.py under installed apps that were commented out for testing purposes.
- To connect user id to skill graph (via login?)
