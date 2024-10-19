# PishPosh (an e-commerce site)

#### API Routes

GET /v1/products

**Meaning:** Will get all products and their IDs as well as the userID of the seller

**Response:** {"Products" : [{"productID", "productname", "userID"}, ...]}

**Response Code:** 200

GET /v1/products/<productID>

**Meaning:** Will get one product based on a valid product ID

**Response:** {"Product": {"productID", "productname", "userID"}}

**Response Code:** 200



GET /v1/users

**Meaning:** Will get all usernames, their IDs, and their first and last names (last name optional)

**Response:** {"Users" : [{"userID", "username", "firstname", "lastname"}, ...]}

**Response Code:** 200

GET /v1/users/<userId>

**Meaning:** Will get one user based on a valid user ID and the products they've listed

**Response:** {"User": {"userID", "username", "firstname", "lastname", "products"}}

**Response Code:** 200



GET /v1/tags

**Meaning:** Will get all tags and their IDs

**Response:** {"Tags" : [{"tagID", "tagname"}, ...]}

**Response Code:** 200

GET /v1/tag/<tagID>

**Meaning:** Will get one tag based on a valid tag ID and the product IDs they're attributed to

**Response:** {"Tag": {"tagID", "tagname", "products"}}

**Response Code:** 200