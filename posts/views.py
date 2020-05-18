from django import forms
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm, FollowForm
from .models import Post, Group, Comment, Follow 
from django.db.models import Count

def index(request):
        post_list = Post.objects.order_by("-pub_date").all()
        paginator = Paginator(post_list, 10) # показывать по 10 записей на странице.

        page_number = request.GET.get("page") # переменная в URL с номером запрошенной страницы
        page = paginator.get_page(page_number) # получить записи с нужным смещением
        return render(request, "index.html", {"page": page, "paginator": paginator})


def group_posts(request, slug):
        group = get_object_or_404(Group, slug=slug)
        posts = Post.objects.filter(group=group).order_by("-pub_date").all()

        paginator = Paginator(posts, 10) 
        page_number = request.GET.get("page") 
        page = paginator.get_page(page_number)
        return render(request, "group.html", {"group": group, "posts": posts, "page": page, "paginator": paginator})


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
        return render(request, "new_post.html", {"form":form})
    form = PostForm()
    return render(request, "new_post.html", {"form":form})


def profile(request, username):
        profile = get_object_or_404(User, username=username)
        post = Post.objects.filter(author=profile).order_by("-pub_date").all()

        paginator = Paginator(post, 10)
        page_number = request.GET.get("page")
        page = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following = Follow.objects.filter(user=request.user, author=profile).exists()
        else:
            following = None
        return render(request, "profile.html", {"profile": profile, "page": page, "paginator": paginator, "post":post, "following":following})

def post_view(request, username, post_id):
        post_view = get_object_or_404(Post, pk=post_id)
        profile = User.objects.get(username=username)
        post = Post.objects.get(pk=post_id)
        posts_count = Post.objects.filter(author__id=profile.id).count()
        form = CommentForm()
        items = Comment.objects.filter(post=post)
        return render(request, "post.html", {"profile": profile, "post": post, "posts_count": posts_count, "form": form, "items": items})

        

@login_required
def post_edit(request, username, post_id):
        post = Post.objects.get(pk=post_id)
        if request.method == "POST":
            form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
            if form.is_valid():
                post = form.save(commit=True)
                post.save()
                return redirect("post", username=post.author.username, post_id=post.pk)
            return render(request, "post_new.html", {"form": form, "post":post})        
        form = PostForm(instance=post)
        return render(request, "post_new.html", {"form": form, "post":post})


@login_required
def add_comment(request, username, post_id):
        author = get_object_or_404(User, username=username)
        post = get_object_or_404(Post, pk=post_id)
        if request.method == "POST":
            form = CommentForm(request.POST or None)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.post = post
                comment.author = request.user
                comment.save()
                return redirect("post", username=post.author.username, post_id=post.pk)


@login_required
def follow_index(request):
    follows = Follow.objects.filter(user=request.user)
    post_list = Post.objects.filter(author__following__in=follows).order_by("-pub_date")
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"paginator":paginator, "page":page})

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_follow = Follow.objects.filter(author=author, user=request.user).exists()
    if author != request.user and not is_follow:
        Follow.objects.create(author=author, user=request.user)
    return redirect("profile", username = username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user)
    if follow.exists():
        follow.delete()
        return redirect("profile", username=username)    


def page_not_found(request, exception):
        return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
        return render(request, "misc/500.html", status=500)