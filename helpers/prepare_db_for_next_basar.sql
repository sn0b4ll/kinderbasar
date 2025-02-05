-- Remove all articles from carts
update article set cart_uuid=NULL;

-- Set all articles to not current
update article set current=0;

-- Delete all carts
delete from cart;

-- Reset the checkin for all users
update user set checkin_done=0;