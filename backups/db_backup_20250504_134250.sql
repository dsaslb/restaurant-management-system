-- Table: alert_logs
-- Table: attendances
-- Table: notifications
-- Table: schedules
-- Table: stores
INSERT INTO stores VALUES (1, '본사', '서울시 강남구', '02-1234-5678', '2025-05-03 14:17:20.760390', '2025-05-03 14:17:20.760417');
-- Table: user_contracts
INSERT INTO user_contracts VALUES (1, 2, '2025-05-03', '2025-08-01', '시급', 9860, '2025-05-03 14:17:25.221943', '2025-05-03 14:17:25.221964', None, None, None, None);
INSERT INTO user_contracts VALUES (2, 3, '2025-05-03', '2025-10-30', '월급', 2000000, '2025-05-03 14:17:25.239699', '2025-05-03 14:17:25.239713', None, None, None, None);
INSERT INTO user_contracts VALUES (3, 4, '2025-05-03', '2025-07-02', '주급', 500000, '2025-05-03 14:17:25.240051', '2025-05-03 14:17:25.240063', None, None, None, None);
-- Table: users
INSERT INTO users VALUES (1, 'admin01', 'pbkdf2:sha256:260000$hfMiRO6s$fc221b6c7d37e3f6872a80ee4b714ac3c628f8e725c0bd40602b9f4a502046ac', '관리자', 'admin', 1, None, None, '2025-05-03 14:17:22.203500', '2025-05-03 14:17:22.203592', None, None, None, None, None, None, None);
INSERT INTO users VALUES (2, 'user_hourly', 'pbkdf2:sha256:260000$0yRWZp3bNRcgmjy5$f21abd3f9603e817fa47f3eb3339c686d53acd4bc9c407df7d50863b5efcdcee', '홍시급', 'employee', 1, None, None, '2025-05-03 14:17:25.016041', '2025-05-03 14:17:25.016051', '시급', 9860, 'gAAAAABoFiV1fYH8DvQRwuNyh-FTcDox2MuDmVydxTMQqKbDDWbve-jLuw5FqTm-UgZOBMPOc6zHMEKfy4cgK8WXi6PITw3hog==', None, None, None, None);
INSERT INTO users VALUES (3, 'user_monthly', 'pbkdf2:sha256:260000$au4u0i6P7tJraiSg$bbb256d6376d6552d14c7b1b3d127db0e7085144540a99bce4ff0c27f1857cfd', '이월급', 'employee', 1, None, None, '2025-05-03 14:17:25.179894', '2025-05-03 14:17:25.179909', '월급', 2000000, 'gAAAAABoFiV1kFUKbu-ElpWFSjwHqsR69sD9vZTxPpGbBuPON-wBbv0NNN9rVRKFQAEnouZZL4ySEfOyzBD1wWvKG6NJ9L8YSw==', None, None, None, None);
INSERT INTO users VALUES (4, 'user_weekly', 'pbkdf2:sha256:260000$VLbk1BWuXU4iO76X$88ec85a362f77d3821e86f29ac6f020511ebf24ed61e97fccaa3fc8d3c1d64b3', '김주급', 'employee', 1, None, None, '2025-05-03 14:17:25.180608', '2025-05-03 14:17:25.180623', '주급', 500000, 'gAAAAABoFiV1wEcY2oziwOTCvH-zEC_VPh0BWcT5Vl26_J-qUAnVl2GGsNPsNUn0kEjWFrvzNYieIf5bFdCDQSKObN04co2i4Q==', None, None, None, None);
-- Table: work_feedbacks
-- Table: work_logs
