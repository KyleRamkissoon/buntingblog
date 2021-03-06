import os
import secrets
from PIL import Image #Using pillow to resize images
from flask import render_template, url_for, flash, redirect, request, abort
from buntingblog import app, db, bcrypt
from buntingblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from buntingblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_simplemde import SimpleMDE

@app.route('/')
@app.route('/home')
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all() #gets all the post each time
    return render_template('home.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username= form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account Created! You can now log in!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title= 'Register', form = form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next') #page routing stuff

            return redirect(next_page) if next_page else redirect(url_for('home')) #redirects to specific page or goes to homepage is there isnt a specific page
        else:
            flash('Login Unsuccessful. Please check information', 'danger')

    return render_template('login.html', title= 'Login', form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

def savePic(form_picture):
    randomHex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename) #dont need filename only the extension
    picture_fn = randomHex + f_ext
    picturepath = os.path.join(app.root_path,'static/pics', picture_fn)

    output_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(output_size) #reszing image

    img.save(picturepath)
    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = savePic(form.picture.data)
            current_user.image_file= picture_file
        current_user.username= form.username.data
        current_user.email= form.email.data
        db.session.commit()
        flash('Your Profile Info has been Updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='pics/'+ current_user.image_file)
    return render_template('account.html', title= 'Profile', image_file=image_file, form=form)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def newPost():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been successfully made!', 'success')
        return redirect(url_for('home'))
    return render_template('createPost.html', title= 'New Post', form = form, legend='New Post')


@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id) #either gets post or returns an error message
    return render_template('post.html', title=post.title, post=post)

@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def updatePost(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403) #manually aborts if the user is not the same user who creates the post
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('createPost.html', title= 'Update Post', form = form, legend='Update Post')

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def deletePost(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your Post has been successfully deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/user/<string:username>')
def userPosts(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).all() #gets all the post each time
    return render_template('userPosts.html', posts=posts, user=user)

