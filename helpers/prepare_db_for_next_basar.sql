-- Remove all articles from carts
update article set cart_uuid=NULL;

-- Delete sold articles
delete from article where sold=1;

-- Set all articles to not current
update article set current=0;

-- Delete all carts
delete from cart;

-- Reset the checkin for all users
update user set checkin_done=0;

-- Delete old articles
delete from article where last_current <= '2024-01-01 00:00:00';

-- Delete all users where there are no articles and they are not organizers
DELETE FROM user WHERE NOT EXISTS (SELECT 1 FROM article a WHERE a.user_id = user.id) AND organizer != 1;
