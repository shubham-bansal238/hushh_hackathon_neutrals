const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const productsRouter = require('./products');

const app = express();
const PORT = 5174;

app.use(cors());
app.use(bodyParser.json());

app.use('/api/products', productsRouter);

app.listen(PORT, () => {
  console.log(`API server running on http://localhost:${PORT}`);
});
