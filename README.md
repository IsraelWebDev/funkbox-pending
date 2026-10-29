# funkbox-pending

The working state of [funkbox](https://github.com/IsraelWebDev/funkbox)'s daily promo. The code and rules are in
funkbox's [`promo/`](https://github.com/IsraelWebDev/funkbox/tree/main/promo); this repo holds what they produce:

- `days/<date>/`: each day's brief (the trend and its sources), on-screen copy, shot list, caption, the reviewer's
  verdict and the text audit
- `posts.jsonl`: every post attempt, with its link or error
- `<date>.mp4`: a reviewed video waiting to be posted, removed once it is on YouTube (X fetches it from here)

Everything is written by the scheduled run; please don't edit it by hand.
