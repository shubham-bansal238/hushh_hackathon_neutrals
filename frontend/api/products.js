const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

const PRODUCTS_PATH = path.join(__dirname, '../src/data/products.json');

// Update product status
router.post('/update-status', (req, res) => {
  const { id, newStatus } = req.body;
  if (!id || !newStatus) return res.status(400).json({ error: 'Missing id or newStatus' });

  fs.readFile(PRODUCTS_PATH, 'utf8', (err, data) => {
    if (err) return res.status(500).json({ error: 'Read error' });
    let json;
    try {
      json = JSON.parse(data);
    } catch (e) {
      return res.status(500).json({ error: 'Parse error' });
    }
    const idx = json.products.findIndex(p => p.id === id);
    if (idx === -1) return res.status(404).json({ error: 'Product not found' });
    json.products[idx].status = newStatus;
    fs.writeFile(PRODUCTS_PATH, JSON.stringify(json, null, 2), err2 => {
      if (err2) return res.status(500).json({ error: 'Write error' });
      res.json({ success: true });
    });
  });
});

module.exports = router;
