from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Post

CACHE_TTL = 60  # seconds


# 🟢 Level 1 & 2: Basic + Granular Cache
class PostList(APIView):
    def get(self, request):
        data = cache.get('all_posts')
        if not data:
            posts = Post.objects.all().values('id', 'title', 'content')
            data = list(posts)
            cache.set('all_posts', data, timeout=CACHE_TTL)
        return Response(data)

    def post(self, request):
        post = Post.objects.create(
            title=request.data.get('title'),
            content=request.data.get('content', ''),
        )
        # 🔵 Level 3: Invalidate list cache on create
        cache.delete('all_posts')
        return Response({'id': post.id, 'title': post.title}, status=status.HTTP_201_CREATED)


# 🟡 Level 2 & 🔵 Level 3: Granular cache + invalidation
class PostDetail(APIView):
    def get(self, request, id):
        cache_key = f'post_{id}'
        data = cache.get(cache_key)
        if not data:
            try:
                post = Post.objects.get(id=id)
            except Post.DoesNotExist:
                return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            data = {'id': post.id, 'title': post.title, 'content': post.content}
            # 🔴 Level 4: Per-post key with timeout
            cache.set(cache_key, data, timeout=CACHE_TTL)
        return Response(data)

    def put(self, request, id):
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        post.title = request.data.get('title', post.title)
        post.content = request.data.get('content', post.content)
        post.save()

        # 🔵 Level 3: Clear both caches on update
        cache.delete(f'post_{id}')
        cache.delete('all_posts')
        return Response({'message': 'Updated'})

    def delete(self, request, id):
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        post.delete()

        # 🔵 Level 3: Clear both caches on delete
        cache.delete(f'post_{id}')
        cache.delete('all_posts')
        return Response({'message': 'Deleted'}, status=status.HTTP_204_NO_CONTENT)
