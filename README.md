# Django REST framework Blog API

The app is build with the **Django REST framework** and uses:
- Docker
- Postgres
- Celery
- RabbitMQ
- Redis
- drf-spectacular for documentation

## Getting started
1. Clone the repository
2. Rename `.env.sample` to `.env` and replace the values
3. Run in your terminal `docker-compose up --build`
4. Now everything should be set up and app's documentation available on http://localhost:8000/api/docs/

## Testing
To run tests:
1. If containers are not running, run in your terminal `docker-compose up`
2. In the second terminal tab, run `docker ps` and get the ID of the app container
3. Run `docker exec -itu 0 <container ID> sh` to get access to the container's shell as a root user
4. Run `python manage.py test` to run all tests or `python manage.py test <app-name>.tests` to run tests for a specific app

## API Endpoints
**User app**
- Use `/api/user/create/` to create a new user 
- Then use `/api/user/token/` to create a token for the created user
- Use `/api/user/profile/` to retrieve user details and update password and user profile details
- Use `/api/user/forgot-password/`to send an email with a link to reset the password.

**Posts app**
- Use `/api/post/posts/` to create a new post and retrieve all posts. Available query params:
  + `tags` - a list of tags ids to filter by. For example `?tags=1,5,20`
  + `sort` - sorting posts by:
    - `title-asc`, `title-desc` - title
    - `comments-asc`, `comments-desc`- number of comments
    - `date-asc`, `date-desc` - `created_at` value
    - `update-asc`, `update-desc` - `updated_at` value
    
  each in ascending or descending order. For example `?sort=comments-asc`.
 
- Use `/api/post/posts/{id}/` to see post details, update and delete a post


- Use `/api/post/tags/` to retrieve all tags
- Use `/api/post/tags/{id}/` to update and delete a tag


- Use `/api/post/comments/` to create a comment
- Use `/api/post/comments/{id}/` to update and delete a comment


- Use `/api/post/postimages/` to create an additional image for a post
- Use `/api/post/postimages/{id}/` to update and delete a post image

- Use `/api/post/votes/` to create a vote of a comment 
- Use `/api/post/votes/{id}/` to delete a vote. There is no option to update it (change the `vote_type` property). If a user decides to change their vote, it will be deleted and then created a new one.


More information about API endpoints, with examples of data that needs to be sent with a request, can be found on http://localhost:8000/api/docs/.
This will provide you with complete and easy-to-use documentation. It also gives the option to use every endpoint of this API.

### More Information
This app uses [djangorestframework-camel-case ](https://github.com/vbabiy/djangorestframework-camel-case) to enable the server to send and receive data in a format that is compatible with TypeScript. This package provides support for camel-case style serialization and deserialization, which is appropriate for the conventions used in Vue.js.
