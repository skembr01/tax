from flask import Flask, render_template, request  # Added request for handling form data
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/sam/dad_ag_tax_2026/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=1)
app.secret_key = 'secret123'

db = SQLAlchemy(app)  # Initialize SQLAlchemy

# Define a model for yearly data
class YearlyData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    gross = db.Column(db.Float, nullable=False)
    social_security = db.Column(db.Float, nullable=False)
    medicare = db.Column(db.Float, nullable=False)
    federal = db.Column(db.Float, nullable=False)
    state = db.Column(db.Float, nullable=False)
    net = db.Column(db.Float, nullable=False)
    total_tax = db.Column(db.Float, nullable=False)

# Define a model for weekly data
class WeeklyData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    gross = db.Column(db.Float, nullable=False)
    social_security = db.Column(db.Float, nullable=False)
    medicare = db.Column(db.Float, nullable=False)
    federal = db.Column(db.Float, nullable=False)
    state = db.Column(db.Float, nullable=False)
    net = db.Column(db.Float, nullable=False)
    total_tax = db.Column(db.Float, nullable=False)

# Define a model for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    yearly_data = db.relationship('YearlyData', backref='user', lazy=True)
    weekly_data = db.relationship('WeeklyData', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.name}>"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'ok'}

# Get taxes
@app.route('/calc_tax', methods=['GET', 'POST'])
def calc_tax():
    ## all current users
    users = User.query.order_by(User.name).all()
    ## result to be provided if GET
    result = None
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        if employee_id:
            user = User.query.get(int(employee_id))
            name = user.name
        elif name:
            name = name.capitalize()
            user = User.query.filter_by(name=name).first()
            if not user:
                user = User(name=name)
                db.session.add(user)
                db.session.commit()
        else:
            return "Please select or add an employee."
        # name = request.form.get('name')  # Get name from form
        # name = name.capitalize()  # Capitalize name
        # get hours
        hours = request.form.get('hours', type=int)  # Get hours from form
        income = hours * 14
        if not name or hours is None:
            return "Please provide both a name and hours."
        """
            State Tax Calculation:
                0 for less than 60, goes up .35 in $10 income increments from 60-1530, 
                then .035% on all income over 1530
        """
        if income < 60:
            state_tax = 0
        elif income >= 1530:
            state_tax = (income * .035) + 51.11
        elif income >= 60 and income < 1530:
            iter_val = .01
            if income < 70:
                state_tax = iter_val
            else:
                iter_wage = 69
            while iter_wage < income:
                iter_val += .35
                iter_wage += 10
                if iter_wage > income + 1000:
                    break
            state_tax = iter_val

        """ Federal Tax Calculation:
                0-234: 0
                235-384: start at 0 and then add 1 for every 10 wage increment
                385-459: start at 15 and then add 2 then 1 for every 15 wage increment
                460-1134: start at 24 that is tax if less than 475 else if x % 4 == 0 add 1 else add 2
                1135-1209: start at 103 and then add 2 for every 15 increment wage
                1210-1374: start at 116, add 4, 3, 3, 3, 4, 3, 3, 4, 3, 3
        """
        if income < 235:
            fed_tax = 0
        elif income > 1374:
            fed_tax = 'Income too high for this calculation.'
        elif income >= 235 and income < 385:
            iter_val = 0
            iter_wage = 234
            while iter_wage < income:
                iter_val += 1
                iter_wage += 10
            fed_tax = iter_val
        elif income >= 385 and income < 460:
            iter_val = 15
            iter_wage = 384
            iter_count = 0
            while iter_wage < income:
                if iter_count % 2 == 0:
                    iter_val += 2
                else:
                    iter_val += 1
                iter_wage += 15
                iter_count += 1
            fed_tax = iter_val
        elif income >= 460 and income < 1135:
            iter_val = 23
            iter_wage = 459
            iter_count = 0
            if income < 475:
                fed_tax = iter_val + 1
            else:
                while iter_wage < income:
                    if iter_count % 4 == 0:
                        iter_val += 1
                    else:
                        iter_val += 2
                    iter_wage += 15
                    iter_count += 1
                fed_tax = iter_val
        elif income >= 1135 and income < 1210:
            iter_val = 103
            iter_wage = 1134
            while iter_wage < income:
                iter_val += 2
                iter_wage += 15
            fed_tax = iter_val
        elif income >= 1210 and income < 1375:
            iter_val = 116
            iter_wage = 1209
            iter_count = 0
            tax_array = [4, 3, 3, 3, 4, 3, 3, 4, 3, 3]
            while iter_wage < income:
                iter_val += tax_array[iter_count]
                iter_wage += 15
                iter_count += 1
            fed_tax = iter_val

        """
            Social Security Tax Calculation:
                6.2% on all income up to $153,000
        """
        soc_sec = income * .062

        """ 
            Medicare Tax Calculation:
                1.45% on all income
        """
        med = income * .0145

        """
            Total tax:
                State Tax + Federal Tax + Social Security Tax + Medicare Tax
        """
        total_tax = state_tax + fed_tax + soc_sec + med

        """
            Net Income Calculation:
                Gross Income - (State Tax + Federal Tax + Social Security Tax + Medicare Tax)
        """
        net_income = income - total_tax

        """
            SQL Insertions:
                User: Insert name into users table
                   Check if name exists in users table, if not, insert name
                Weekly Data: Insert income and tax into weekly_data table
                Yearly Data: Insert total income and total tax into yearly_data table
                    Sum new weeks up with old week for user
        """
        # user
        user = User.query.filter_by(name=name).first()
        if not user:
            user = User(name=name)
            db.session.add(user)
            db.session.commit()
        # weekly data
        week_number = datetime.date.today().isocalendar()[1]
        weekly_data = WeeklyData(user_id=user.id, week=week_number, hours=hours, gross=income, social_security=soc_sec, medicare=med, federal=fed_tax, state=state_tax, net=net_income, total_tax=total_tax)
        db.session.add(weekly_data)
        db.session.commit()
        # yearly data
        yearly_data = YearlyData.query.filter_by(user_id=user.id, year=datetime.date.today().year).first()
        if yearly_data:
            yearly_data.hours += hours
            yearly_data.gross += income
            yearly_data.social_security += soc_sec
            yearly_data.medicare += med
            yearly_data.federal += fed_tax
            yearly_data.state += state_tax
            yearly_data.net += net_income
            yearly_data.total_tax += total_tax
        else:
            yearly_data = YearlyData(user_id=user.id, year=datetime.date.today().year, hours=hours, gross=income, social_security=soc_sec, medicare=med, federal=fed_tax, state=state_tax, net=net_income, total_tax=total_tax)
            db.session.add(yearly_data)
        db.session.commit()
        
        result = f"{name}<br><br>Hours: {hours}<br><br>Gross Income: ${income:.2f}<br><br>Social Security: ${soc_sec:.2f}<br><br>Medicare: ${med:.2f}<br><br>Federal: ${fed_tax:.2f}<br><br>State: ${state_tax:.2f}<br><br>Net Income: ${net_income:.2f}<br><br>Total Tax: ${total_tax:.2f}"
    return render_template('calc_tax.html', result=result, users=users)
    """return '''
        <form method="post">
            Name: <input type="text" name="name"><br>
            Hours: <input type="number" name="hours" step="1"><br>
            <input type="submit" value="Calculate">
        </form>
    '''
    """

from flask import Flask, render_template, request, redirect, url_for, session

app.secret_key = "your_secret_key"

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "LarryPattisamJosh126062823":
            session["logged_in"] = True
            return redirect(url_for("user_menu"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/user_menu')
def user_menu():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    users = User.query.order_by(User.name).all()
    return render_template('user_menu.html', users=users)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables only if they don't exist
    app.run(debug=True)