const express = require('express');
const app = express();

const usersApi = require('./api/users.js');

app.use(express.json());
app.use('/api/users', usersApi);


const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Listening on port ${PORT}`));