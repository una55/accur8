#using flask username = admin & password = admin ; port 5000
#test server for testing brute_force.py 
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <h2>Login Page</h2>
  <form method="POST" action="/login">
    <input type="text" name="username" placeholder="Username" /><br><br>
    <input type="password" name="password" placeholder="Password" /><br><br>
    <input type="submit" value="Login" />
  </form>
  {% if error %}
    <p style="color:red;">{{ error }}</p>
  {% endif %}
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = request.form.get("username")
        passwd = request.form.get("password")
        if user == "admin" and passwd == "admin":
            return "Welcome admin!"
        else:
            error = "Invalid credentials"
    return render_template_string(HTML, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
