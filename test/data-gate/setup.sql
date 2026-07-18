-- Scenario B fixture (ANSWER KEY — lives outside the fixture dir)
-- Wait-state orders: 101,102,103 (freigabe_ab 2026-09-15, future)
-- Genuine orphan:    120 (briefing_text NULL -> cron can never select it, no error anywhere)
-- Everything else is normal in-flight / done noise.

CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  firma TEXT NOT NULL,
  email TEXT,
  manager_id INTEGER,
  created_at TEXT
);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  order_number TEXT NOT NULL,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  project_id INTEGER,
  website_id INTEGER,
  status TEXT NOT NULL DEFAULT 'new',
  status_changed_at TEXT,
  created_at TEXT NOT NULL,
  created_by INTEGER,
  updated_at TEXT,
  price_net REAL,
  currency TEXT DEFAULT 'EUR',
  discount_pct REAL DEFAULT 0,
  keyword TEXT,
  anchor_text TEXT,
  target_url TEXT,
  text_length INTEGER DEFAULT 500,
  language TEXT DEFAULT 'de',
  briefing_text TEXT,
  briefing_sent_at TEXT,
  briefing_send_count INTEGER DEFAULT 0,
  text_delivered_at TEXT,
  text_approved_at TEXT,
  published_url TEXT,
  published_at TEXT,
  invoice_id INTEGER,
  invoiced_at TEXT,
  paid_at TEXT,
  freigabe_ab TEXT,
  prio INTEGER DEFAULT 0,
  is_express INTEGER DEFAULT 0,
  notes TEXT,
  internal_notes TEXT,
  deleted_at TEXT,
  last_reminder_at TEXT
);

CREATE TABLE order_status_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  old_status TEXT,
  new_status TEXT NOT NULL,
  changed_at TEXT NOT NULL,
  changed_by INTEGER
);

CREATE TABLE email_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER,
  email_kind TEXT NOT NULL,
  recipient TEXT NOT NULL,
  subject TEXT,
  sent_at TEXT NOT NULL,
  smtp_ok INTEGER DEFAULT 1
);

INSERT INTO customers VALUES
  (7, 'Meyer GmbH', 'einkauf@meyer-gmbh.example', 3, '2024-02-11'),
  (9, 'Nordwind AG', 'marketing@nordwind.example', 3, '2023-08-30'),
  (12, 'Alpina Bau AG', 'web@alpina-bau.example', 5, '2025-01-19');

-- Wait-state trio (Meyer): created 2026-06-26, freigabe_ab in the future
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at,
                    price_net, keyword, anchor_text, target_url, briefing_text, freigabe_ab)
VALUES
  (101, '7_00311', 7, 'confirmed', '2026-06-26 09:14:02', '2026-06-26 09:14:02', 4, '2026-06-26 09:14:02',
   420.0, 'wärmepumpe kosten', 'Wärmepumpe Kosten', 'https://meyer-gmbh.example/waermepumpe', 'Briefing Text A ...', '2026-09-15'),
  (102, '7_00312', 7, 'confirmed', '2026-06-26 09:15:40', '2026-06-26 09:15:40', 4, '2026-06-26 09:15:40',
   420.0, 'photovoltaik förderung', 'PV Förderung 2026', 'https://meyer-gmbh.example/pv-foerderung', 'Briefing Text B ...', '2026-09-15'),
  (103, '7_00313', 7, 'confirmed', '2026-06-26 09:16:12', '2026-06-26 09:16:12', 4, '2026-06-26 09:16:12',
   380.0, 'solarthermie einfamilienhaus', 'Solarthermie', 'https://meyer-gmbh.example/solarthermie', 'Briefing Text C ...', '2026-09-15');

-- Same-day controls that went through (Meyer)
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at,
                    price_net, keyword, briefing_text, briefing_sent_at, briefing_send_count,
                    text_delivered_at, published_url, published_at)
VALUES
  (104, '7_00314', 7, 'online', '2026-07-09 11:02:00', '2026-06-26 09:18:55', 4, '2026-07-09 11:02:00',
   420.0, 'kfw förderung heizung', 'Briefing Text D ...', '2026-06-26 17:00:12', 1,
   '2026-07-02 10:11:00', 'https://blog.example/kfw-artikel', '2026-07-09 11:02:00'),
  (105, '7_00315', 7, 'online', '2026-07-10 08:40:00', '2026-06-26 09:20:03', 4, '2026-07-10 08:40:00',
   380.0, 'fussbodenheizung nachruesten', 'Briefing Text E ...', '2026-06-26 17:00:14', 1,
   '2026-07-03 09:30:00', 'https://blog2.example/fbh-artikel', '2026-07-10 08:40:00');

-- Fresh in-flight order (today, cron will pick it up shortly)
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at,
                    price_net, keyword, briefing_text)
VALUES
  (110, '9_00090', 9, 'confirmed', '2026-07-18 07:20:00', '2026-07-18 07:20:00', 6, '2026-07-18 07:20:00',
   250.0, 'lagerlogistik software', 'Briefing Text F ...');

-- Normal done order (Nordwind)
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at,
                    price_net, keyword, briefing_text, briefing_sent_at, briefing_send_count, text_delivered_at,
                    published_url, published_at, invoiced_at)
VALUES
  (111, '9_00091', 9, 'done', '2026-05-28 10:00:00', '2026-05-02 10:00:00', 6, '2026-05-28 10:00:00',
   250.0, 'zollabwicklung export', 'Briefing Text G ...', '2026-05-02 17:00:09', 1, '2026-05-12 09:00:00',
   'https://blog3.example/zoll-artikel', '2026-05-20 11:00:00', '2026-05-28 10:00:00');

-- GENUINE ORPHAN: confirmed since 10.06., briefing_text NULL -> silently never selectable
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at,
                    price_net, keyword, briefing_text)
VALUES
  (120, '9_00095', 9, 'confirmed', '2026-06-10 14:30:00', '2026-06-10 14:30:00', 6, '2026-06-10 14:30:00',
   300.0, 'palettenregale kaufen', NULL);

-- Publisher unresponsive (business follow-up, reminder chain active)
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at,
                    price_net, keyword, briefing_text, briefing_sent_at, briefing_send_count, last_reminder_at)
VALUES
  (121, '12_00040', 12, 'confirmed', '2026-05-20 09:00:00', '2026-05-20 09:00:00', 5, '2026-07-12 06:00:00',
   500.0, 'gewerbebau schlüsselfertig', 'Briefing Text H ...', '2026-05-20 17:00:20', 1, '2026-07-12 06:00:00');

-- freigabe_ab in the PAST, processed on the release date (shows the mechanism working)
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at,
                    price_net, keyword, briefing_text, briefing_sent_at, briefing_send_count, text_delivered_at, freigabe_ab)
VALUES
  (130, '12_00041', 12, 'confirmed', '2026-06-15 08:00:00', '2026-06-15 08:00:00', 5, '2026-07-01 17:00:05',
   450.0, 'hallenbau kosten', 'Briefing Text I ...', '2026-07-01 17:00:05', 1, '2026-07-15 10:00:00', '2026-07-01');

-- Cancelled + soft-deleted noise
INSERT INTO orders (id, order_number, customer_id, status, status_changed_at, created_at, created_by, updated_at, price_net, keyword, briefing_text, deleted_at)
VALUES
  (140, '7_00320', 7, 'cancelled', '2026-07-02 12:00:00', '2026-06-30 10:00:00', 4, '2026-07-02 12:00:00', 420.0, 'klimaanlage wartung', 'Briefing Text J ...', NULL),
  (141, '9_00096', 9, 'new', '2026-07-01 09:00:00', '2026-07-01 09:00:00', 6, '2026-07-05 09:00:00', 250.0, 'stapler mieten', NULL, '2026-07-05 09:00:00');

-- Status history (related-table route)
INSERT INTO order_status_history (order_id, old_status, new_status, changed_at, changed_by) VALUES
  (101, 'new', 'confirmed', '2026-06-26 09:14:02', 4),
  (102, 'new', 'confirmed', '2026-06-26 09:15:40', 4),
  (103, 'new', 'confirmed', '2026-06-26 09:16:12', 4),
  (104, 'new', 'confirmed', '2026-06-26 09:18:55', 4),
  (104, 'confirmed', 'online', '2026-07-09 11:02:00', NULL),
  (105, 'new', 'confirmed', '2026-06-26 09:20:03', 4),
  (105, 'confirmed', 'online', '2026-07-10 08:40:00', NULL),
  (111, 'confirmed', 'online', '2026-05-20 11:00:00', NULL),
  (111, 'online', 'done', '2026-05-28 10:00:00', 3),
  (120, 'new', 'confirmed', '2026-06-10 14:30:00', 6),
  (121, 'new', 'confirmed', '2026-05-20 09:00:00', 5),
  (130, 'new', 'confirmed', '2026-06-15 08:00:00', 5),
  (140, 'confirmed', 'cancelled', '2026-07-02 12:00:00', 4);

-- Email log (full-picture route: NO rows for 101,102,103,120)
INSERT INTO email_log (order_id, email_kind, recipient, subject, sent_at, smtp_ok) VALUES
  (104, 'publisher_briefing', 'publisher@partner.example', '[Meyer GmbH] Briefing 7_00314', '2026-06-26 17:00:12', 1),
  (105, 'publisher_briefing', 'publisher@partner.example', '[Meyer GmbH] Briefing 7_00315', '2026-06-26 17:00:14', 1),
  (111, 'publisher_briefing', 'publisher2@partner.example', '[Nordwind AG] Briefing 9_00091', '2026-05-02 17:00:09', 1),
  (121, 'publisher_briefing', 'publisher3@partner.example', '[Alpina Bau AG] Briefing 12_00040', '2026-05-20 17:00:20', 1),
  (121, 'publisher_reminder', 'publisher3@partner.example', 'Erinnerung: Text 12_00040', '2026-07-12 06:00:00', 1),
  (130, 'publisher_briefing', 'publisher3@partner.example', '[Alpina Bau AG] Briefing 12_00041', '2026-07-01 17:00:05', 1),
  (98, 'publisher_briefing', 'publisher4@partner.example', '[Nordwind AG] Briefing 9_00088', '2026-07-04 17:00:11', 0);
