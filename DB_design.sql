CREATE TABLE `user` (
  `_id` ObjectId PRIMARY KEY,
  `username` string,
  `displayName` string,
  `email` string,
  `phone` string,
  `sex` string,
  `birth` date,
  `avatar` string,
  `google` boolean,
  `facebook` boolean,
  `password` string,
  `addresses` ObjectId[],
  `createdAt` datetime,
  `vouchers` ObjectId[]
);

CREATE TABLE `admin` (
  `_id` ObjectId PRIMARY KEY,
  `username` string,
  `displayName` string,
  `email` string,
  `phone` string,
  `sex` string,
  `birth` date,
  `avatar` string,
  `password` string,
  `createdAt` datetime
);

CREATE TABLE `address` (
  `_id` ObjectId PRIMARY KEY,
  `receiver` string,
  `detail` string,
  `ward` string,
  `district` string,
  `province` string,
  `phone` string,
  `default` boolean,
  `createdAt` datetime
);

CREATE TABLE `brand` (
  `_id` ObjectId PRIMARY KEY,
  `name` string,
  `description` string
);

CREATE TABLE `product` (
  `_id` ObjectId PRIMARY KEY,
  `name` string,
  `originalPrice` number,
  `sold` number,
  `rate` number,
  `stock` number,
  `discount` number,
  `description` string,
  `images` string[],
  `brandId` ObjectId,
  `sizeTable` string,
  `categoryId` ObjectId,
  `createdAt` datetime
);

CREATE TABLE `parentCategory` (
  `_id` ObjectId PRIMARY KEY,
  `name` string
);

CREATE TABLE `childCategory` (
  `_id` ObjectId PRIMARY KEY,
  `name` string,
  `parentId` ObjectId
);

CREATE TABLE `color` (
  `_id` ObjectId PRIMARY KEY,
  `productId` ObjectId,
  `colorName` string,
  `image` string,
  `tags` string[]
);

CREATE TABLE `size` (
  `_id` ObjectId PRIMARY KEY,
  `productId` ObjectId,
  `sizeName` string,
  `tags` string[]
);

CREATE TABLE `voucher` (
  `_id` ObjectId PRIMARY KEY,
  `name` string,
  `code` string,
  `description` string,
  `discount` number,
  `minValue` string,
  `start` datetime,
  `expired` datetime,
  `category` ObjectId[]
);

CREATE TABLE `review` (
  `_id` ObjectId PRIMARY KEY,
  `productId` ObjectId,
  `rate` number,
  `description` string,
  `image` string,
  `likeCount` number,
  `dislikeCount` number,
  `createdAt` datetime,
  `userId` ObjectId,
  `userAvatar` string,
  `orderId` ObjectId
);

CREATE TABLE `cart` (
  `_id` ObjectId PRIMARY KEY,
  `userId` ObjectId,
  `cart_products` object[]
);

CREATE TABLE `wishlist` (
  `_id` ObjectId PRIMARY KEY,
  `userId` ObjectId,
  `save_products` object[]
);

CREATE TABLE `payment` (
  `_id` ObjectId PRIMARY KEY,
  `orderId` ObjectId,
  `method` string,
  `status` string,
  `paid_at` datetime
);

CREATE TABLE `order` (
  `_id` ObjectId PRIMARY KEY,
  `userId` ObjectId,
  `addressId` ObjectId,
  `products` object[],
  `shippingFee` number,
  `voucherId` ObjectId,
  `VAT` number,
  `totalPrice` number,
  `paymentInfo` string[],
  `paid` boolean,
  `status` string,
  `createdAt` datetime
);

CREATE TABLE `notif` (
  `_id` ObjectId PRIMARY KEY,
  `userId` ObjectId,
  `notif` notifDetail[]
);

CREATE TABLE `notifDetail` (
  `_id` ObjectId PRIMARY KEY,
  `title` string,
  `content` string,
  `type` string,
  `read` boolean,
  `createdAt` datetime
);

ALTER TABLE `user` ADD FOREIGN KEY (`addresses`) REFERENCES `address` (`_id`);

ALTER TABLE `user` ADD FOREIGN KEY (`vouchers`) REFERENCES `voucher` (`_id`);

ALTER TABLE `product` ADD FOREIGN KEY (`brandId`) REFERENCES `brand` (`_id`);

ALTER TABLE `product` ADD FOREIGN KEY (`categoryId`) REFERENCES `childCategory` (`_id`);

ALTER TABLE `childCategory` ADD FOREIGN KEY (`parentId`) REFERENCES `parentCategory` (`_id`);

ALTER TABLE `color` ADD FOREIGN KEY (`productId`) REFERENCES `product` (`_id`);

ALTER TABLE `size` ADD FOREIGN KEY (`productId`) REFERENCES `product` (`_id`);

ALTER TABLE `voucher` ADD FOREIGN KEY (`category`) REFERENCES `childCategory` (`_id`);

ALTER TABLE `review` ADD FOREIGN KEY (`productId`) REFERENCES `product` (`_id`);

ALTER TABLE `review` ADD FOREIGN KEY (`userId`) REFERENCES `user` (`_id`);

ALTER TABLE `review` ADD FOREIGN KEY (`orderId`) REFERENCES `order` (`_id`);

ALTER TABLE `cart` ADD FOREIGN KEY (`userId`) REFERENCES `user` (`_id`);

ALTER TABLE `cart` ADD FOREIGN KEY (`cart_products`) REFERENCES `product` (`_id`);

ALTER TABLE `wishlist` ADD FOREIGN KEY (`userId`) REFERENCES `user` (`_id`);

ALTER TABLE `wishlist` ADD FOREIGN KEY (`save_products`) REFERENCES `product` (`_id`);

ALTER TABLE `payment` ADD FOREIGN KEY (`orderId`) REFERENCES `order` (`_id`);

ALTER TABLE `order` ADD FOREIGN KEY (`userId`) REFERENCES `user` (`_id`);

ALTER TABLE `order` ADD FOREIGN KEY (`addressId`) REFERENCES `address` (`_id`);

ALTER TABLE `order` ADD FOREIGN KEY (`voucherId`) REFERENCES `voucher` (`_id`);

ALTER TABLE `notif` ADD FOREIGN KEY (`userId`) REFERENCES `user` (`_id`);

ALTER TABLE `notif` ADD FOREIGN KEY (`notif`) REFERENCES `notifDetail` (`_id`);
