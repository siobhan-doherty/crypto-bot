

# Check Data in MongoDB


## Access MongoDB shell inside the container
```bash
docker exec -it crypto_mongo mongosh -u <USER_NAME> -p <PASSWORD> --authenticationDatabase admin
```
**Tip:**
Replace `<USER_NAME>` and `<PASSWORD>` with your actual MongoDB credentials.

## Working in MongoDB
```bash
# List databases

db.adminCommand('listDatabases')


# Switch to 'cryptobot' database
use cryptobot

# List collections
db.getCollectionNames()

# Rename collection
db.streaming_data.renameCollection('streaming_data_1m')

# Create a backup to test the init dag with airflow
db.historical_data_15m.aggregate([{ $match: {} }, { $out: "historical_data_15m_buckup" }]);

# Sample data inspection
db.historical_data_15m.findOne()
db.historical_data_15m.countDocuments()
db.historical_data_15m.findOne({ "symbol": "BTCUSDT" })
db.historical_data_15m.findOne({ "symbol": "ETHUSDT" })

db.streaming_data_1m.findOne()
db.streaming_data_1m.countDocuments()
db.streaming_data_1m.countDocuments({ "symbol": "BTCUSDT" })
db.streaming_data_1m.countDocuments({ "symbol": "ETHUSDT" })
db.streaming_data_1m.findOne({ "symbol": "BTCUSDT" })
db.streaming_data_1m.findOne({ "symbol": "ETHUSDT" })

# Drop collections (use with caution)
db.streaming_data.drop()
db.historical_data_15m.drop()

# Earliest open_time
db.historical_data_15m.find({}, {open_time: 1, _id: 0}).sort({ open_time: 1 }).limit(1)
  .forEach(doc => print(new Date(Number(doc.open_time))));

# Latest open_time
db.historical_data_15m.find({}, {open_time: -1, _id: 0}).sort({ open_time: -1 }).limit(1)
  .forEach(doc => print(new Date(Number(doc.open_time))));

# check How many candles are in BTCUSDT
var symbol = "BTCUSDT"; 
var earliest = db.historical_data_15m.find({symbol: symbol}).sort({ open_time: 1 }).limit(1).toArray()[0].open_time;
var latest   = db.historical_data_15m.find({symbol: symbol}).sort({ open_time: -1 }).limit(1).toArray()[0].open_time;
earliest = Number(earliest);
latest = Number(latest);

var count = db.historical_data_15m.countDocuments({
  symbol: symbol,
  open_time: { $gte: earliest, $lte: latest }
});
print('Symbol:', symbol);
print('Actual:', count);

var expected = Math.round((latest - earliest) / (15 * 60 * 1000)) + 1;
print('Expected:', expected);
print('Difference:', expected - count);

# how many duplicates are in BTCUSDT
db.historical_data_15m.aggregate([
  { $match: { symbol: "BTCUSDT" } },
  { $group: { _id: "$open_time", count: { $sum: 1 } } },
  { $match: { count: { $gt: 1 } } },
  { $count: "duplicates" }
])

# check How many candles are in ETHUSDT
var symbol = "ETHUSDT";
var earliest = db.historical_data_15m.find({symbol: symbol}).sort({ open_time: 1 }).limit(1).toArray()[0].open_time;
var latest   = db.historical_data_15m.find({symbol: symbol}).sort({ open_time: -1 }).limit(1).toArray()[0].open_time;
earliest = Number(earliest);
latest = Number(latest);

var count = db.historical_data_15m.countDocuments({
  symbol: symbol,
  open_time: { $gte: earliest, $lte: latest }
});
print('Symbol:', symbol);
print('Actual:', count);

var expected = Math.round((latest - earliest) / (15 * 60 * 1000)) + 1;
print('Expected:', expected);
print('Difference:', expected - count);

# how many duplicates are in ETHUSDT
db.historical_data_15m.aggregate([
  { $match: { symbol: "ETHUSDT" } },
  { $group: { _id: "$open_time", count: { $sum: 1 } } },
  { $match: { count: { $gt: 1 } } },
  { $count: "duplicates" }
])
```

