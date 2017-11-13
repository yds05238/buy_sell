# some imports
from flask import Flask, render_template, flash, redirect, url_for, session, request, send_from_directory
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, validators, FileField, IntegerField, PasswordField
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename
from shutil import rmtree
from functools import wraps
import MySQLdb
import os


# connect to database in localhost to create database and their tables

database = MySQLdb.connect("localhost", "OSAMA", "OSAMA")
cursor = database.cursor()
# cursor.execute("DROP DATABASE IF EXISTS buy_sell;")
cursor.execute("CREATE DATABASE IF NOT EXISTS buy_sell DEFAULT CHARSET UTF8")
database.select_db('buy_sell')
# cursor.execute("DROP TABLE IF EXISTS users;")
# cursor.execute("DROP TABLE IF EXISTS products;")


cursor.execute("CREATE TABLE IF NOT EXISTS users(\
                id INT(11) AUTO_INCREMENT PRIMARY KEY,\
                permission VARCHAR(10) NOT NULL,\
                first_name VARCHAR(100) NOT NULL,\
                last_name VARCHAR(100) NOT NULL,\
                email VARCHAR(100) NOT NULL,\
                gender VARCHAR(10) NOT NULL,\
                country VARCHAR(50) NOT NULL,\
                username VARCHAR(100) NOT NULL,\
                password VARCHAR(100) NOT NULL,\
                files TEXT NOT NULL,\
                register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP );")

cursor.execute("CREATE TABLE IF NOT EXISTS products(\
                id INT(11) AUTO_INCREMENT PRIMARY KEY,\
                category VARCHAR(100) NOT NULL,\
                product_name VARCHAR(255) NOT NULL,\
                description TEXT NOT NULL,\
                price INT(10) NOT NULL,\
                discount INT(10) NOT NULL,\
                files TEXT NOT NULL,\
                create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")

cursor.execute("CREATE TABLE IF NOT EXISTS categories (category VARCHAR(255) PRIMARY KEY);")

database.close()


app = Flask(__name__)


# application configuration

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'buy_sell'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# website icon

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/vnd.microsoft.icon')


# home page

@app.route('/')
def home():
    return render_template('home.html')


# preview product page

@app.route('/preview_production/<id>/')
def preview_production(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id={}".format(id))
    product = cur.fetchone()
    cur.close()
    return render_template('preview_production.html', product=product)


# admin registration page

@app.route('/admin/register')
def admin_register():
    return render_template('register.html')


# admin login page

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = BINARY %s AND permission='admin'", [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candidate, password):
                session['admin_logged_in'] = True
                cur.close()
                flash('Now You Are Logged In ', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Wrong Password!'
                return render_template('admin_login.html', error=error)
        else:
            error = 'Username Can Not Be Found!'
            return render_template('admin_login.html', error=error)
    return render_template('admin_login.html')


# check if admin is still logged in 

def is_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session :
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('admin_login'))
    return wrap


# admin log out

@app.route('/admin/logout')
@is_admin_logged_in
def admin_logout():
    session.clear()
    flash('You Are Now Logged Out', 'success')
    return redirect(url_for('admin_login'))


# admin dashboard page

@app.route('/admin/', methods=['post', 'get'])
@is_admin_logged_in
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(id) FROM products")
    products = cur.fetchone()
    count_products = products['COUNT(id)']
    cur.execute("SELECT COUNT(id) FROM users")
    users = cur.fetchone()
    count_users = users['COUNT(id)']
    cur.execute("SELECT COUNT(category) FROM categories")
    categories = cur.fetchone()
    count_categories = categories['COUNT(category)']
    cur.close()
    return render_template('index.html', count_products=count_products, count_users=count_users, count_categories=count_categories)


# product validators form

class AddProductForm(Form):
    product_name = StringField('Name Of Product', [validators.InputRequired(), validators.length(min=1, max=180)])
    description = TextAreaField('Description', [validators.InputRequired()])
    price = IntegerField('Price', [validators.InputRequired()])
    discount = StringField('Discount Percentage %')
    # files = FileField('Add picture to Your Product', [validators.InputRequired()])


# admin add new product page

@app.route('/admin/add_product', methods=['post', 'get'])
@is_admin_logged_in
def add_product():
    form = AddProductForm(request.form)
    cur = mysql.connection.cursor()
    cur.execute("SELECT category FROM categories")
    categories = cur.fetchall()
    cur.close()

    if request.method == 'POST' and form.validate():
        product_name = form.product_name.data

        cur = mysql.connection.cursor()
        cur.execute("SELECT product_name FROM products WHERE product_name = BINARY %s", [product_name])
        res = cur.fetchone()
        if product_name in str(res):
            msg = "Product Name Already Exists"
            return render_template('admin_add_production.html', form=form, msg=msg)
        else:

            file = request.files['file']
            if file.filename == '':
                flash('You Have to Select a File!', 'warning')
            if file and allowed_file(file.filename):
                try:
                    rmtree(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product_name))
                    os.makedirs(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product_name))
                except:
                    os.makedirs(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product_name))
                filename = secure_filename(file.filename)
                dir = r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product_name)
                file.save(os.path.join(dir, filename))
                category = request.form['categories']
                description = form.description.data.lower()
                price = form.price.data
                discount = form.discount.data
                
                if discount != '' and discount != ' ':
                    p = (int(price) * int(discount)) / 100
                    cur = mysql.connection.cursor()
                    cur.execute("INSERT INTO products(category, product_name, description, price, discount, files)\
                                                 VALUES(%s, %s, %s, %s, %s, %s)", \
                                (category, product_name, description, price, p, filename))
                    mysql.connection.commit()
                    cur.close()
                    flash('Your Product is published successfully!', 'success')
                    return redirect(url_for('admin_dashboard'))

                if discount == "" or discount == " ":
                    p = 0
                    cur = mysql.connection.cursor()
                    cur.execute("INSERT INTO products(category, product_name, description, price, discount, files)\
                                                 VALUES(%s, %s, %s, %s, %s, %s)", \
                                (category, product_name, description, price, p, filename))
                    mysql.connection.commit()
                    cur.close()
                    flash('Your Product is published successfully!', 'success')
                    return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_production.html', form=form, categories=categories)
                                
                # cur = mysql.connection.cursor()
                # cur.execute("INSERT INTO products(category, product_name, description, price, discount, files)\
                #              VALUES(%s, %s, %s, %s, %s, %s)", \
                #             (category, product_name, description, price, p, filename))
                # mysql.connection.commit()
                # cur.close()
                # flash('Your Product is published successfully!', 'success')
                # return redirect(url_for('admin_dashboard'))
    # return render_template('admin_add_production.html', form=form, categories=categories)


# admin edit product page

@app.route('/admin/edit_product/<id>', methods=['post', 'get'])
@is_admin_logged_in
def edit_product(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT category FROM categories")
    categories = cur.fetchall()
    cur.close()
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id={}".format(id))
    product = cur.fetchone()
    cur.close()
    form = AddProductForm(request.form)
    form.product_name.data = product['product_name']
    form.description.data = product['description']
    form.price.data = product['price']
    # form.discount.data = product['discount']
    
    
    d = (int(product['discount']) * 100)/int(form.price.data)
    form.discount.data = int(d)
    
    
    if request.method == 'POST' and form.validate():
        product_name = request.form['product_name']
        file = request.files['file']
        if file and allowed_file(file.filename):
            rmtree(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product['product_name']))
            os.makedirs(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product_name))
            filename = secure_filename(file.filename)
            dir = r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product_name)
            file.save(os.path.join(dir, filename))
        
            category = request.form['categories']
            description = request.form['description']
            price = request.form['price']
            discount = request.form['discount']

            p = (int(price) * int(discount)) / 100
            
            cur = mysql.connection.cursor()
            cur.execute("UPDATE products SET category=%s, product_name=%s, description=%s, price=%s,\
                         discount=%s, files=%s WHERE id=%s", \
                        (category, product_name, description, price, p, filename, id))
            mysql.connection.commit()
            cur.close()
            flash('Your Product Has been Edited successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        elif file.filename == '' or 'file' not in request.files:
            os.rename(os.path.join(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product['product_name'])),
                      os.path.join(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product_name)))
            category = request.form['categories']
            description = request.form['description']
            price = request.form['price']
            discount = request.form['discount']

            p = (int(price) * int(discount)) / 100
            
            cur = mysql.connection.cursor()
            cur.execute("UPDATE products SET category=%s, product_name=%s, description=%s, price=%s,\
                                     discount=%s WHERE id=%s", \
                        (category, product_name, description, price, p, id))
            mysql.connection.commit()
            cur.close()
            flash('Your Product Has been Edited successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_edit_production.html', form=form, categories=categories)


# admin delete product

@app.route('/admin/delete_product/<id>', methods=['post', 'get'])
@is_admin_logged_in
def delete_product(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT product_name FROM products WHERE id = %s", [id])
    name = cur.fetchone()
    n = name['product_name']
    rmtree(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(n))
    cur.execute("DELETE FROM products WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Your Product Has been Deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# admin create user account validator form

class AdduserForm(Form):
    first_name = StringField('First Name', [validators.InputRequired()])
    last_name = StringField('Last Name', [validators.InputRequired()])
    username = StringField('User Name', [validators.InputRequired()])
    password = PasswordField('Password',
                             [validators.DataRequired(), validators.Length(min=6, max=100),
                              validators.EqualTo('confirm', message='Passwords Do Not Match')])
    confirm = PasswordField('Confirm Password', [validators.DataRequired()])


# admin create user account page

@app.route('/admin/add_user', methods=['post', 'get'])
@is_admin_logged_in
def add_user():
    form = AdduserForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE username = BINARY %s", [username])
        res = cur.fetchone()
        if username in str(res):
            msg = "User Name Already Exists"
            return render_template('admin_add_user.html', form=form, msg=msg)
        else:
            permission = request.form['permissions']
            first_name = form.first_name.data.lower()
            last_name = form.last_name.data.lower()
            email = request.form['email'].lower()
            gender = request.form['gender']
            country = request.form['country']
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data))
            file = request.files['file']
            if file.filename == '':
                flash('You Have to Select a File!', 'warning')
            try:
                rmtree(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\users\{}".format(username))
                os.makedirs(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\users\{}".format(username))
            except:
                os.makedirs(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\users\{}".format(username))
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                dir = r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\users\{}".format(username)
                file.save(os.path.join(dir, filename))
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO users(permission, first_name, last_name,\
                             email, gender, country, username, password, files)\
                             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", \
                            (permission, first_name, last_name, email, gender,\
                             country, username, password, filename))
                mysql.connection.commit()
                cur.close()
                flash('You Have Created a User Account successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_user.html', form=form)


# admin delete user 

@app.route('/admin/delete_user/<id>', methods=['post', 'get'])
@is_admin_logged_in
def delete_user(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT username FROM users WHERE id = %s", [id])
    name = cur.fetchone()
    n = name['username']
    rmtree(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\users\{}".format(n))
    cur.execute("DELETE FROM users WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('You Have Deleted User Account successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# admin add new category validator form

class CategoryForm(Form):
    category = StringField('Category', [validators.InputRequired(), validators.length(min=1, max=100)])
    

# admin add new category page

@app.route('/admin/add_category', methods=['post', 'get'])
@is_admin_logged_in
def add_category():
    form = CategoryForm(request.form)
    if request.method == 'POST' and form.validate():
        category = form.category.data.lower()
        if category == ' ':
            flash('You Should Type A Word!', 'warning')
            return redirect(url_for('add_category'))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO categories (category) VALUES(%s);", ([category]))
        mysql.connection.commit()
        cur.close()
        flash('You Have Added New Category successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_category.html', form=form)


# admin edit category page

@app.route('/admin/edit_category/<current_category>', methods=['post', 'get'])
@is_admin_logged_in
def edit_category(current_category):
        cur = mysql.connection.cursor()
        cur.execute("SELECT category FROM categories Where category=%s;", [current_category])
        cat = cur.fetchone()
        cur.close()
        form = CategoryForm(request.form)
        form.category.data = cat['category']
        if request.method == 'POST' and form.validate():
            category = request.form['category'].lower()
            if category == ' ':
                flash('You Should Type A Word!', 'warning')
                return redirect(url_for('add_category'))
            cur = mysql.connection.cursor()
            cur.execute("UPDATE categories SET category=%s WHERE category=%s;", ([category], [current_category]))
            cur.execute("UPDATE products SET category=%s WHERE category=%s", \
                        ([category], [current_category]))
            mysql.connection.commit()
            cur.close()
            flash('You Have Edited Category successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_edit_category.html', form=form)


# admin delete category 

@app.route('/admin/delete_category/<category>', methods=['post', 'get'])
@is_admin_logged_in
def delete_category(category):
        cur = mysql.connection.cursor()
        prod = cur.execute("SELECT product_name FROM products WHERE category=%s", [category])
        if prod > 0:
            flash('You Have products in This category', 'success')
            # pass
        products = cur.fetchall()
        for product in products:
                rmtree(r"C:\Users\OSAMA\Desktop\buy_sell\static\uploads\products\{}".format(product['product_name']))
        cur.execute("DELETE FROM products WHERE category=%s", [category])
        cur.execute("DELETE FROM categories Where category=%s;", [category])
        mysql.connection.commit()
        cur.close()        
        flash("You Have Deleted Category With it's products successfully!", 'success')
        return redirect(url_for('admin_dashboard'))


# admin preview all products table page

@app.route('/admin/products_table')
@is_admin_logged_in
def products_table():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return render_template('products_table.html', products=products)


# admin preview all categories table page

@app.route('/admin/categories_table')
@is_admin_logged_in
def categories_table():
    cur = mysql.connection.cursor()
    cur.execute("SELECT category FROM categories")
    categories = cur.fetchall()
    cur.close()
    return render_template('categories_table.html', categories=categories)


# admin preview all users table page

@app.route('/admin/users_table')
@is_admin_logged_in
def users_table():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.close()
    return render_template('users_table.html', users=users)


# run whole application function

if __name__ == '__main__':
    app.secret_key = 'osama_blog'
    app.run(debug=True)
