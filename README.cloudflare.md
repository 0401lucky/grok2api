# Grok2API锛圕loudflare Workers / Pages锛欴1 + KV锛?

杩欎釜浠撳簱宸茬粡鏂板 **Cloudflare Workers / Pages** 鍙儴缃茬増鏈紙TypeScript锛夈€?

> 涓€閿儴缃插墠缃潯浠讹細鑻ヤ娇鐢?GitHub Actions 宸ヤ綔娴侊紝璇峰厛鍦ㄤ粨搴?Secrets 閰嶇疆 `CLOUDFLARE_API_TOKEN` 涓?`CLOUDFLARE_ACCOUNT_ID`銆? 
> Docker 涓€閿惎鍔ㄥ叆鍙ｄ粛鏄?`docker compose up -d`锛岃鍙傝€?`readme.md`銆?

## 鍔熻兘姒傝

- **D1锛圫QLite锛?*锛氭寔涔呭寲 Tokens / API Keys / 绠＄悊鍛樹細璇?/ 閰嶇疆 / 鏃ュ織
- **KV**锛氱紦瀛?`/images/*` 鐨勫浘鐗?瑙嗛璧勬簮锛堜粠 `assets.grok.com` 浠ｇ悊鎶撳彇锛?
- **姣忓ぉ 0 鐐圭粺涓€娓呴櫎**锛氶€氳繃 KV `expiration` + Workers Cron 瀹氭椂娓呯悊鍏冩暟鎹紙`wrangler.toml` 宸查厤缃紝榛樿鎸夊寳浜椂闂?00:00锛?
- **鍓嶇绉诲姩绔€傞厤涓€鑷寸敓鏁?*锛歐orkers 涓?FastAPI/Docker 澶嶇敤鍚屼竴濂?`/static/*` 璧勬簮锛屽寘鍚墜鏈虹鎶藉眽瀵艰埅銆佽〃鏍兼í鍚戞粴鍔ㄣ€丄PI Key 灞呬腑鎮诞鏂板寮圭獥绛変氦浜?
- **妯″瀷闆嗗悎涓庝富 README 瀵归綈**锛氫弗鏍肩Щ闄ゆ棫妯″瀷鍚嶅苟鍚屾鏂板妯″瀷锛堝惈 `grok-4.20-beta`锛?
- **鑱婂ぉ閲嶈瘯鑳藉姏涓€鑷寸敓鏁?*锛歚/chat` 涓?`/admin/chat` 鏀寔鈥滈噸璇曚笂涓€鏉″洖绛斺€濅笌鈥滃浘鐗囧姞杞藉け璐ョ偣鍑婚噸璇曗€?

> 鍘?Python/FastAPI 鐗堟湰浠嶄繚鐣欑敤浜庢湰鍦?Docker锛汣loudflare 閮ㄧ讲璇锋寜鏈枃浠惰蛋 Worker 鐗堟湰銆?

---

## 鍗囩骇/杩佺Щ锛堜笉涓㈡暟鎹級

- Workers 浠ｇ爜鏇存柊涓嶄細娓呯┖ D1 / KV锛氬彧瑕佺户缁粦瀹氬悓涓€涓?D1 鏁版嵁搴撳拰 KV Namespace锛岃处鎴锋暟鎹紙Tokens / Keys / 閰嶇疆 / 鏃ュ織锛変笉浼氫涪銆?
- 缂撳瓨涓嶄細鍥犱负鍗囩骇鑰岀珛鍒讳涪澶憋細KV 涓殑缂撳瓨瀵硅薄浼氭寜鈥滄湰鍦?0 鐐光€濊繃鏈燂紙expiration锛夊苟鐢?Cron 姣忓ぉ娓呯悊鍏冩暟鎹紝鍗囩骇鍚庝粛淇濇寔涓€澶╀竴娓呯悊銆?
- 娉ㄦ剰涓嶈闅忔剰鏀?`wrangler.toml` 閲岀殑 `name` / D1/KV 缁戝畾 ID锛涘鏋滀綘鐢?GitHub Actions 涓€閿儴缃诧紝涔熻淇濇寔 Worker 鍚嶇О涓€鑷达紝鍚﹀垯鍙兘鍒涘缓鏂扮殑 D1/KV 璧勬簮瀵艰嚧鈥滅湅璧锋潵鍍忎涪鏁版嵁鈥濄€?
- 绠＄悊鍛樿处鍙峰瘑鐮佷笉浼氳榛樿鍊艰鐩栵細杩佺Щ鑴氭湰浣跨敤 `INSERT OR IGNORE` 鍒濆鍖栭粯璁ら厤缃紱濡傛灉浣犱箣鍓嶅凡鍦ㄩ潰鏉块噷淇敼杩囪处鍙?瀵嗙爜锛屽崌绾у悗浼氫繚鐣欏師鍊笺€?

## 0) 鍓嶇疆鏉′欢

- Node.js 18+锛堜綘鏈満宸叉弧瓒冲嵆鍙級
- 宸插畨瑁?鍙繍琛?`wrangler`锛堟湰浠撳簱浣跨敤 `npx wrangler`锛?
- Cloudflare 璐﹀彿锛堝凡鎵樼鍩熷悕鏇村ソ锛屼究浜庣粦瀹氳嚜瀹氫箟鍩熷悕锛?

---

## 1) 鍒濆鍖栵紙鏈湴锛?

```bash
npm install
```

鐧诲綍 Cloudflare锛?

```bash
npx wrangler login
```

---

## 2) 鍒涘缓骞剁粦瀹?D1锛堜粎鎵嬪姩閮ㄧ讲闇€瑕侊級

鍒涘缓 D1锛?

```bash
npx wrangler d1 create grok2api
```

鎶婅緭鍑洪噷鐨?`database_id` 濉繘 `wrangler.toml`锛?

- `wrangler.toml` 鐨?`database_id = "REPLACE_WITH_D1_DATABASE_ID"`

搴旂敤杩佺Щ锛堜細鍒涘缓鎵€鏈夎〃锛夛細

```bash
npx wrangler d1 migrations apply grok2api --remote
```

浣犱篃鍙互鐩存帴鎸夌粦瀹氬悕鎵ц锛堟帹鑽愶紝閬垮厤鏀瑰悕鍚庡嚭閿欙級锛?

```bash
npx wrangler d1 migrations apply DB --remote
```

杩佺Щ鏂囦欢鍦細
- `migrations/0001_init.sql`
- `migrations/0002_r2_cache.sql`锛堟棫鐗堬紝宸插簾寮冿級
- `migrations/0003_kv_cache.sql`锛堟柊鐗?KV 缂撳瓨鍏冩暟鎹級

---

## 3) 鍒涘缓骞剁粦瀹?KV锛堜粎鎵嬪姩閮ㄧ讲闇€瑕侊級

KV Namespace 寤鸿鍛藉悕涓猴細`grok2api-cache`

濡傛灉浣犱娇鐢?GitHub Actions锛堟帹鑽愶級锛屼細鍦ㄩ儴缃插墠鑷姩锛?
- 鍒涘缓锛堟垨澶嶇敤锛塂1 鏁版嵁搴擄細`grok2api`
- 鍒涘缓锛堟垨澶嶇敤锛塊V namespace锛歚grok2api-cache`
- 鑷姩缁戝畾鍒?Worker锛堟棤闇€浣犳墜鍔ㄥ～浠讳綍 ID锛?

濡傛灉浣犳墜鍔ㄩ儴缃诧紝鍙互鑷繁鍒涘缓 KV namespace 骞舵妸 ID 濉繘 `wrangler.toml`锛?

```bash
npx wrangler kv namespace create grok2api-cache
```

鐒跺悗鎶婅緭鍑虹殑 `id` 濉埌 `wrangler.toml`锛?
- `[[kv_namespaces]]`
  - `binding = "KV_CACHE"`
  - `id = "<浣犵殑namespace id>"`

---

## 4) 閰嶇疆姣忓ぉ 0 鐐规竻鐞嗭紙Cron + 鍙傛暟锛?

`wrangler.toml` 宸查粯璁ら厤缃紙鎸夊寳浜椂闂?00:00锛夛細

- `CACHE_RESET_TZ_OFFSET_MINUTES = "480"`锛氭椂鍖哄亸绉伙紙鍒嗛挓锛夛紝榛樿 UTC+8
- `crons = ["0 16 * * *"]`锛氭瘡澶?16:00 UTC锛? 鍖椾含鏃堕棿 00:00锛夎Е鍙戞竻鐞?
- `KV_CACHE_MAX_BYTES = "26214400"`锛氭渶澶х紦瀛樺璞″ぇ灏忥紙KV 鍗曞€兼湁澶у皬闄愬埗锛屽缓璁?鈮?25MB锛?
- `KV_CLEANUP_BATCH = "200"`锛氭竻鐞嗘壒閲忥紙鍒犻櫎 KV key + D1 鍏冩暟鎹級

---

## 5) 閮ㄧ讲鍒?Workers锛堟帹鑽愶紝鍔熻兘鏈€瀹屾暣锛?

閮ㄧ讲锛?

```bash
npx wrangler deploy
```

閮ㄧ讲鍚庢鏌ワ細
- `GET https://<浣犵殑鍩熷悕鎴杦orkers.dev>/health`
- 鎵撳紑 `https://<浣犵殑鍩熷悕鎴杦orkers.dev>/login`

锛堝彲閫夛級鍐掔儫娴嬭瘯锛?

```bash
python scripts/smoke_test.py --base-url https://<浣犵殑鍩熷悕鎴杦orkers.dev>
```

榛樿绠＄悊鍛樿处鍙峰瘑鐮侊細
- 榛樿鐢ㄦ埛鍚?`admin`锛涢粯璁ゅ瘑鐮佷负鍗犱綅鍊硷紝闇€鍏堟敼涓哄己瀵嗙爜鍚庡啀鐧诲綍

寮虹儓寤鸿鐧诲綍鍚庣珛鍒讳慨鏀癸紙鍦ㄣ€岃缃€嶉噷鏀?`admin_password` / `admin_username`锛夈€?

---

## 5.1) GitHub Actions 涓€閿儴缃诧紙鎺ㄨ崘锛?

浠撳簱宸插寘鍚伐浣滄祦锛歚.github/workflows/cloudflare-workers.yml`锛屽湪 `main` 鍒嗘敮 push 鏃朵細鑷姩锛?

1. `npm ci` + `npm run typecheck`
2. 鑷姩鍒涘缓/澶嶇敤 D1 + KV锛屽苟鐢熸垚 `wrangler.ci.toml`
3. `wrangler d1 migrations apply DB --remote --config wrangler.ci.toml`
4. `wrangler deploy`

### 浠撳簱绾ч儴缃茶嚜妫€锛堝缓璁級

鍦ㄨЕ鍙戜竴閿儴缃插墠锛屽彲鍏堝湪浠撳簱鏍圭洰褰曡繍琛岋細

```bash
uv run --with pytest pytest -q
npm run typecheck
python scripts/check_model_catalog_sync.py
npx wrangler deploy --dry-run --config wrangler.toml
docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml -f docker-compose.build.yml config
```

瑙﹀彂绛栫暐淇濇寔涓嶅彉锛?
- `push` 鍒?`main`锛氳嚜鍔ㄨЕ鍙?Cloudflare 閮ㄧ讲浣滀笟
- `workflow_dispatch`锛氬彲鎵嬪姩閫夋嫨 `cloudflare/docker/both`
- `v*` tag锛氱敤浜?Docker 鏋勫缓鍙戝竷閾捐矾

浣犻渶瑕佸湪 GitHub 浠撳簱閲岄厤缃?Secrets锛圫ettings 鈫?Secrets and variables 鈫?Actions锛夛細

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`锛堝繀濉級

> 鎻愮ず锛歚CLOUDFLARE_API_TOKEN` 寤鸿浣跨敤 **API Token**锛堜笉瑕佺敤 Global API Key锛夛紝骞剁‘淇濊嚦灏戝寘鍚?**Workers Scripts / D1 / Workers KV Storage** 鐨勭紪杈戞潈闄愶紱鍚﹀垯宸ヤ綔娴佸彲鑳芥棤娉曡嚜鍔ㄥ垱寤?澶嶇敤 D1/KV 鎴栭儴缃?Worker銆?

鐒跺悗鐩存帴 push 鍒?`main`锛堟垨鍦?Actions 椤甸潰鎵嬪姩 Run workflow锛夊嵆鍙竴閿儴缃诧紙鏃犻渶浣犳墜鍔ㄥ垱寤?濉啓 D1 鎴?KV 鐨?ID锛夈€?

> 娉ㄦ剰锛氭鐗堟湰涓嶅啀浣跨敤 R2銆侴itHub Actions 浼氳嚜鍔ㄥ垱寤?澶嶇敤 D1 涓?KV锛屼絾浣犱粛闇€鍦?GitHub 閰嶅ソ `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID`銆?
>
> 鍙﹀锛歚app/static/_worker.js` 鏄?Pages Advanced Mode 鐨勫叆鍙ｆ枃浠躲€俉orkers 閮ㄧ讲鏃朵細琚?`app/static/.assetsignore` 鎺掗櫎锛岄伩鍏嶈褰撴垚闈欐€佽祫婧愪笂浼犲鑷撮儴缃插け璐ャ€?

---

## 6) 缁戝畾鑷畾涔夊煙鍚嶏紙浣犳湁 CF 鎵樼鍩熷悕锛?

鍦?Cloudflare Dashboard锛?

1. Workers & Pages 鈫?閫夋嫨 `grok2api` 杩欎釜 Worker
2. Settings / Triggers锛堜笉鍚?UI 鍙兘鐣ユ湁宸紓锛?
3. 鎵惧埌 **Custom Domains** 鈫?Add
4. 閫夋嫨浣犵殑鍩熷悕骞跺垱寤?

缁戝畾瀹屾垚鍚庯紝鐩存帴鐢ㄤ綘鐨勫煙鍚嶈闂?`/login` 涓?`/v1/*` 鍗冲彲銆?

---

## 7) 鍚庡彴鍒濆鍖栭厤缃紙蹇呴』锛?

鐧诲綍 `/admin/token` 鍚庤嚦灏戦厤缃紙`/manage` 浠嶄繚鐣欎负鍏煎鍏ュ彛锛屼細璺宠浆锛夛細

1. **Tokens**锛氭坊鍔?`sso` 鎴?`ssoSuper`
2. **璁剧疆**锛?
   - `dynamic_statsig`锛堝缓璁紑鍚級
   - 鎴栬€呭叧闂姩鎬佸苟濉啓 `x_statsig_id`
   - 锛堝彲閫夛級濉啓 `cf_clearance`锛堝彧濉€硷紝涓嶈 `cf_clearance=` 鍓嶇紑锛?
   - 锛堝彲閫夛級寮€鍚?`video_poster_preview`锛氬皢杩斿洖鍐呭涓殑 `<video>` 鏇挎崲涓?Poster 棰勮鍥撅紙榛樿鍏抽棴锛?
   - 锛堝彲閫夛級`image_generation_method`锛歚legacy`锛堥粯璁わ紝绋冲畾锛夋垨 `imagine_ws_experimental`锛堝疄楠屾€ф柊鏂规硶锛屽け璐ヨ嚜鍔ㄥ洖閫€鏃ф柟娉曪級
3. **Keys**锛氬垱寤?API Key锛岀敤浜庤皟鐢?`/v1/*`

---

## 8) 鎺ュ彛

- POST /v1/chat/completions (supports stream: true)
- GET /v1/models (model set aligns with `readme.md`, including latest additions/removals)
- GET /v1/images/method: returns current image-generation mode (legacy or imagine_ws_experimental) for /chat and /admin/chat UI switching
- POST /v1/images/generations: experimental mode supports size (aspect-ratio mapping) and concurrency (1..3)
- POST /v1/images/edits: only accepts grok-imagine-1.0-edit
- GET /images/<img_path>: reads from KV cache; on miss fetches assets.grok.com and writes back to KV (daily expiry/cleanup policy)
- Note: Workers KV single-value size is limited (recommended <= 25MB); most video players use Range requests, which may bypass KV hits
- Admin APIs: /api/*

### 8.1) 绠＄悊鍚庡彴 API 鍏煎璇箟锛堜笌 FastAPI 涓€鑷达級

- GET /api/v1/admin/tokens adds fields (compatible): token_type, quota_known, heavy_quota, heavy_quota_known
- POST /api/v1/admin/keys/update returns 404 when key does not exist
- Quota semantics: remaining_queries = -1 means unknown quota; frontend should use quota_known / heavy_quota_known for judgement

---
## 9) 閮ㄧ讲鍒?Pages锛堝彲閫夛紝浣嗕笉鎺ㄨ崘鐢ㄤ簬鈥滃畾鏃舵竻鐞嗏€濓級

浠撳簱宸叉彁渚?Pages Advanced Mode 鍏ュ彛锛?
- `app/static/_worker.js`

閮ㄧ讲闈欐€佺洰褰曪細

```bash
npx wrangler pages deploy app/static --project-name <浣犵殑Pages椤圭洰鍚? --commit-dirty
```

鐒跺悗鍦?Pages 椤圭洰璁剧疆閲屾坊鍔犵粦瀹氾紙鍚嶇О蹇呴』鍖归厤浠ｇ爜锛夛細
- D1锛氱粦瀹氬悕 `DB`
- KV锛氱粦瀹氬悕 `KV_CACHE`

娉ㄦ剰锛?
- **鑷姩娓呯悊渚濊禆 Cron Trigger**锛岀洰鍓嶆洿鎺ㄨ崘鐢?Workers 閮ㄧ讲璇ラ」鐩互淇濊瘉瀹氭椂娓呯悊绋冲畾杩愯銆?

---

## 10) Worker 鍑虹珯鏇村€惧悜缇庡尯锛堝彲閫夛級

鏈粨搴撻粯璁ゅ湪 `wrangler.toml` 灏?Workers 鐨?Placement 鍥哄畾鍦ㄧ編鍥斤紙Targeted Placement锛夛細

```toml
[placement]
region = "aws:us-east-1"
```

杩欎細璁?Worker 鐨勬墽琛屼綅缃洿绋冲畾鍦伴潬杩戠編鍥藉尯鍩燂紝浠庤€岃鍑虹珯鏇村亸鍚戠編鍖猴紙瀵逛笂娓稿湪缇庡尯鐨勫満鏅洿鍙嬪ソ锛夈€?

濡傞渶璋冩暣锛氭妸 `region` 鏀规垚浣犳兂瑕佺殑鍖哄煙锛堜緥濡?`aws:us-west-2`锛夈€?
濡傞渶鍏抽棴锛氬垹闄?`wrangler.toml` 涓殑 `[placement]` 娈佃惤鍗冲彲锛堟仮澶嶉粯璁ょ殑杈圭紭灏辫繎鎵ц锛夈€?

---

## 11) 鍙戝竷鍚庨獙璇侊紙寤鸿锛?

閮ㄧ讲鍚庡彲鎵ц浠ヤ笅鏈€灏忔鏌ワ細

1. 鍩虹鍋ュ悍涓庣櫥褰曢〉锛?
   - `GET /health`
   - `GET /login`
2. 绠＄悊椤靛彲璁块棶鎬э細
   - `GET /admin/token`
   - `GET /admin/keys`
3. 绉诲姩绔洖褰掞紙寤鸿浣跨敤 `390x844`锛夛細
   - `/admin/keys`锛氱偣鍑烩€滄柊澧?Key鈥濆悗搴斾负灞呬腑鎮诞寮圭獥锛堟湁閬僵锛屽彲鐐归伄缃╁叧闂紝鍙?`Esc` 鍏抽棴锛?
   - 椤堕儴瀵艰埅锛氭墜鏈虹搴斾负鎶藉眽鑿滃崟锛堝彲鎵撳紑/鍏抽棴锛岀偣鍑昏彍鍗曢」鍚庤嚜鍔ㄦ敹璧凤級
   - Token/Keys/Cache 琛ㄦ牸锛氬簲淇濇寔妯悜婊氬姩锛屼笉搴斿帇纰庡垪甯冨眬
4. 鍙€?smoke test锛?

```bash
python scripts/smoke_test.py --base-url https://<浣犵殑鍩熷悕鎴杦orkers.dev>
```

