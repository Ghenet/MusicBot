import os
import secrets
from PIL import Image
from flask import render_template,url_for,flash, redirect, request, abort
from musicbot import app , db, bcrypt
from musicbot.forms import RegistrationForm ,LoginForm , UpdateAccountForm , PostForm
from musicbot.models import  User , Post
from flask_login import login_user , current_user,logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    #grabs all the data from the db
    posts = Post.query.all()
    return  render_template('home.html', posts_data=posts)
  

@app.route('/profile')
def profile():
     return render_template('profile.html',title='Hey About')  


@app.route('/register', methods=['GET','POST'])
def register():
    print('in register')
    # if current_user.is_authenticated:
    #     print('in if')
    #     return redirect(url_for('home'))
    form = RegistrationForm()
    print(request.form)
    if form.validate_on_submit():
        print('in other if')
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!You are now able to log in','success')
        return redirect(url_for('login'))      
    return render_template('register.html',title='Register', form=form)



@app.route('/login', methods =['GET','POST']) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form =LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password , form.password.data):
             login_user(user, remember=form.remember.data)
             next_page = request.args.get('next')   #dont really know what this is doing , gotta refer back to part 6 at 43:00
             return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful.Please check email or password','danger')
    return render_template('login.html',title='Login', form=form)            


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)
    #resize the image before saving it 
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return  picture_fn

#account route
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email    
    image_file = url_for('static', filename='images/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)    

#create-post route
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',form=form,legend='Add your favorite song!') 

#route for a specific post
@app.route("/post/<int:post_id>")
def post(post_id):
    #get_or_404 will return 404 err msg if not found
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

#route for updating a post
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)    
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':    
        form.title.data = post.title   #populates the input textfield with the old data
        form.content.data = post.content  #populates the input textfield with the old data
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Song')    