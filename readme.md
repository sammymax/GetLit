# GetLit
Integrates with Spotify to find artist merchandise on Amazon you might like!

Todo:
- Find a way to get better results (ex. Future returns terrible results right now; Collectibles is not the only category that we should look at, probably)
- Somehow search all artists at once; Amazon API has a 1 query/sec rate limit, so right now, 5 artist searches takes around 5 seconds
- Handle >1 user at once by executing queries in another thread? Flask is bad with concurrency
- Make front end not ugly
