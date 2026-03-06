# Grok2API

鏈」鐩负瀵?[chenyme/grok2api](https://github.com/chenyme/grok2api) 鐨勪簩娆′慨鏀逛笌澧炲己銆?

**涓枃** | [English](docs/README.en.md)

> [!NOTE]
> 鏈」鐩粎渚涘涔犱笌鐮旂┒锛屼娇鐢ㄨ€呭繀椤诲湪閬靛惊 Grok 鐨?**浣跨敤鏉℃** 浠ュ強 **娉曞緥娉曡** 鐨勬儏鍐典笅浣跨敤锛屼笉寰楃敤浜庨潪娉曠敤閫斻€?

鍩轰簬 **FastAPI** 閲嶆瀯鐨?Grok2API锛屽叏闈㈤€傞厤鏈€鏂?Web 璋冪敤鏍煎紡锛屾敮鎸佹祦/闈炴祦寮忓璇濄€佸浘鍍忕敓鎴?缂栬緫銆佹繁搴︽€濊€冿紝鍙锋睜骞跺彂涓庤嚜鍔ㄨ礋杞藉潎琛′竴浣撳寲銆?

<img width="1941" height="1403" alt="screenshot" src="docs/assets/screenshot-2026-02-05-064737.png" />

<br>

## Cloudflare Workers / Pages锛團ork 澧炲己锛?

鏈粨搴撻澶栨彁渚?Cloudflare Workers / Pages锛圱ypeScript锛孌1 + KV锛夌増鏈紝閫傚悎鍦?Cloudflare 涓婅繍琛屼笌浠ｇ悊鍑虹珯銆?

- 閮ㄧ讲涓庨厤缃鏄庯細`README.cloudflare.md`
- 涓€閿儴缃插伐浣滄祦锛歚.github/workflows/cloudflare-workers.yml`
  - 涓€閿儴缃插墠缃潯浠讹細浠撳簱闇€閰嶇疆 `CLOUDFLARE_API_TOKEN` 涓?`CLOUDFLARE_ACCOUNT_ID`銆?

## 浣跨敤璇存槑

### 濡備綍鍚姩

- 鏈湴寮€鍙?

```
需要 Python 3.13+

uv sync

uv run main.py

# 锛堝彲閫夛級鍚姩鍚庤嚜妫€
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

- 椤圭洰閮ㄧ讲

```
git clone <你的仓库地址>

# 杩涘叆椤圭洰鐩綍
cd grok2api

# 鐩存帴鎷夊彇闀滃儚鍚姩锛堥粯璁わ級
docker compose up -d

# 鏇存柊鍒版渶鏂伴暅鍍?
docker compose pull
docker compose up -d

# 浠庡綋鍓嶄粨搴撴簮鐮佹瀯寤哄苟鍚姩锛堝彲閫夛級
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build

# 锛堝彲閫夛級鍚姩鍚庤嚜妫€
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

### 浠撳簱绾ч儴缃茶嚜妫€

鍦ㄦ墽琛屼竴閿儴缃插墠锛屽缓璁厛鍦ㄤ粨搴撴牴鐩綍杩愯锛?

```bash
uv run --with pytest pytest -q
npm run typecheck
python scripts/check_model_catalog_sync.py
npx wrangler deploy --dry-run --config wrangler.toml
docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml -f docker-compose.build.yml config
```

> 濡傛灉鎷夊彇闀滃儚鏃舵姤 `denied`锛氳鏄?GHCR 闀滃儚涓嶅彲鍖垮悕鎷夊彇锛堟湭鍏紑鎴栭渶瑕佺櫥褰曪級銆備綘鍙互鍏堟墽琛?`docker login ghcr.io`锛屾垨鍦?`.env` 閲岃缃?`GROK2API_IMAGE` 鎸囧悜浣犺嚜宸辩殑鍏紑闀滃儚锛涗篃鍙互鐢ㄤ笂闈㈢殑 `--build` 浠庢簮鐮佹瀯寤鸿繍琛屻€?

> 鍙€夛細澶嶅埗 `.env.example` 涓?`.env`锛屽彲閰嶇疆绔彛/鏃ュ織/瀛樺偍绛夛紱骞跺彲閫氳繃 `COMPOSE_PROFILES` 涓€閿惎鐢?`redis/pgsql/mysql`锛堣 `.env.example` 鍐呯ず渚嬶級銆?

> 閮ㄧ讲涓€鑷存€ц鏄庯細鏈湴锛團astAPI锛? Docker / Cloudflare Workers 鍏辩敤鍚屼竴濂楃鐞嗗姛鑳借涔夛紙Token 绛涢€夈€丄PI Key 绠＄悊銆佸悗鍙扮鐞嗘帴鍙ｈ涔変竴鑷达級銆?
> 涓婃父鍏抽敭鍚屾锛?026-02-20锛夛細宸插悓姝ヨ亰澶╅〉鈥滈噸璇曚笂涓€鏉″洖绛斺€濅笌鈥滃浘鐗囧姞杞藉け璐ョ偣鍑婚噸璇曗€濓紝涓夐儴缃蹭笅琛屼负涓€鑷淬€?
> Cloudflare 鍙€氳繃 `.github/workflows/cloudflare-workers.yml` 涓€閿儴缃诧紙闇€鍏堥厤缃笂杩颁袱涓?Secrets锛夛紝Docker 浠嶄繚鎸?`docker compose up -d` 涓€閿惎鍔ㄣ€?

### 绠＄悊闈㈡澘

璁块棶鍦板潃锛歚http://<host>:8000/login`

榛樿鐢ㄦ埛鍚嶄负 `admin`锛?*榛樿瀵嗙爜涓哄崰浣嶅€煎苟浼氳鐧诲綍鎺ュ彛鎷掔粷**銆傝鍏堝湪閰嶇疆涓皢 `app.app_key` 鏀逛负寮哄瘑鐮佸悗鍐嶇櫥褰曘€?
甯哥敤椤甸潰锛?
- `http://<host>:8000/admin/token`锛歍oken 绠＄悊锛堝鍏?瀵煎嚭/鎵归噺鎿嶄綔/鑷姩娉ㄥ唽锛?
- `http://<host>:8000/admin/keys`锛欰PI Key 绠＄悊锛堢粺璁?绛涢€?鏂板/缂栬緫/鍒犻櫎锛?
- `http://<host>:8000/admin/datacenter`锛氭暟鎹腑蹇冿紙甯哥敤鎸囨爣 + 鏃ュ織鏌ョ湅锛?
- `http://<host>:8000/admin/config`锛氶厤缃鐞嗭紙鍚嚜鍔ㄦ敞鍐屾墍闇€閰嶇疆锛?
- `http://<host>:8000/admin/cache`锛氱紦瀛樼鐞嗭紙鏈湴缂撳瓨 + 鍦ㄧ嚎璧勪骇锛?

### 鎵嬫満绔€傞厤锛堝叏绔欙級

- 宸茶鐩栭〉闈細`/login`銆乣/admin/token`銆乣/admin/keys`銆乣/admin/cache`銆乣/admin/config`銆乣/admin/datacenter`銆乣/chat`銆乣/admin/chat`銆?
- 鍚庡彴椤堕儴瀵艰埅鍦ㄦ墜鏈虹鏀逛负鎶藉眽鑿滃崟锛堟敮鎸侊細鎵撳紑/鍏抽棴銆佺偣鍑婚伄缃╁叧闂€佺偣鍑昏彍鍗曢」鍚庤嚜鍔ㄦ敹璧枫€乣Esc` 鍏抽棴锛夈€?
- 琛ㄦ牸鍦ㄦ墜鏈虹淇濇寔鈥滄í鍚戞粴鍔ㄤ紭鍏堚€濓紝涓嶅帇缂╁垪缁撴瀯锛圱oken/API Key/缂撳瓨琛ㄦ牸琛屼负涓€鑷达級銆?
- Toast 鍦ㄧ獎灞忔敼涓哄乏鍙宠竟璺濊嚜閫傚簲锛屼笉鍐嶅浐瀹氭渶灏忓搴﹀鑷存孩鍑恒€?
- 搴曢儴鎵归噺鎿嶄綔鏉★紙Token/缂撳瓨锛夊湪鎵嬫満绔敼涓哄叏瀹藉簳閮ㄥ崱鐗囨牱寮忥紝鍑忓皯閬尅涓绘搷浣溿€?
- 涓夐儴缃蹭竴鑷存€э細涓婅堪閫傞厤浣跨敤鍚屼竴濂楅潤鎬佽祫婧愶紝鍦ㄦ湰鍦?FastAPI / Docker / Cloudflare Workers 涓嬭涓轰竴鑷淬€?

### Token 绠＄悊澧炲己锛堢瓫閫?+ 鐘舵€佸垽瀹氾級

- 鏀寔绫诲瀷绛涢€夛細`sso`銆乣supersso`锛堝彲缁勫悎锛夈€?
- 鏀寔鐘舵€佺瓫閫夛細`娲昏穬`銆乣澶辨晥`銆乣棰濆害鐢ㄥ敖`锛堝彲缁勫悎锛屾寜骞堕泦璇箟锛夈€?
- 鎻愪緵鈥滅粨鏋滆鏁扳€濆拰鈥滄竻绌虹瓫閫夆€濄€?
- 绛涢€夊悗鍕鹃€?鍏ㄩ€?鎵归噺鍒锋柊/鎵归噺鍒犻櫎鍧囧熀浜?Token 鍞竴鍊硷紝閬垮厤杩囨护鍚庤绱㈠紩閿欎綅瀵艰嚧璇搷浣溿€?
- 鐘舵€佸垽瀹氳鍒欙細
  - `澶辨晥`锛歚status` 涓?`invalid/expired/disabled`
  - `棰濆害鐢ㄥ敖`锛歚status = cooling`锛屾垨锛坄quota_known = true` 涓?`quota <= 0`锛夛紝鎴栵紙super 涓?`heavy_quota_known = true` 涓?`heavy_quota <= 0`锛?
  - `娲昏穬`锛氶潪澶辨晥涓旈潪棰濆害鐢ㄥ敖
- 绫诲瀷鏄犲皠瑙勫垯锛歚ssoBasic -> sso`锛宍ssoSuper -> supersso`锛堟帴鍙ｅ瓧娈?`token_type` 涓?`sso` / `ssoSuper`锛夈€?

### API Key 绠＄悊澧炲己

- 椤甸潰鏂板缁熻鍗＄墖锛氭€绘暟銆佸惎鐢ㄣ€佺鐢ㄣ€佷粖鏃ラ搴︾敤灏姐€?
- 宸ュ叿鏍忔敮鎸侊細鍚嶇О/Key 鎼滅储銆佺姸鎬佺瓫閫夛紙鍏ㄩ儴/鍚敤/绂佺敤/棰濆害鐢ㄥ敖锛夈€侀噸缃瓫閫夈€?
- 鏂板 API Key 寮圭獥澧炲己锛?
  - 灞呬腑鎮诞寮圭獥锛堥伄缃╁眰 + 缂╂斁鍏ュ満鍔ㄧ敾锛?
  - 鏀寔鐐瑰嚮閬僵鍏抽棴銆乣Esc` 鍏抽棴
  - 绉诲姩绔脊绐楀唴瀹瑰彲婊氬姩涓旂綉鏍煎竷灞€鑷€傚簲
  - 鑷姩鐢熸垚 Key
  - 棰濆害棰勮锛堟帹鑽?涓嶉檺锛?
  - 鎻愪氦涓鐢ㄦ寜閽紝闃叉閲嶅鎻愪氦
  - 鍒涘缓鎴愬姛鍚庢敮鎸佷竴閿鍒?Key
- 閿欒鎻愮ず浼樺寲锛氬墠绔紭鍏堝睍绀哄悗绔?`detail/error/message`锛岄伩鍏嶁€滃垱寤哄け璐?鏇存柊澶辫触鈥濇棤涓婁笅鏂囥€?
- 鏇存柊涓嶅瓨鍦ㄧ殑 Key 浼氳繑鍥?`404`锛團astAPI 涓?Workers 涓€鑷达級銆?

### 鑷姩娉ㄥ唽锛圱oken 绠＄悊 -> 娣诲姞 -> 鑷姩娉ㄥ唽锛?

鏀寔涓ょ鏂瑰紡锛?
- 鐩存帴娣诲姞 Token锛堟墜鍔?鎵归噺瀵煎叆锛?
- 鑷姩娉ㄥ唽骞惰嚜鍔ㄥ啓鍏?Token 姹?

鑷姩娉ㄥ唽鐗规€э細
- 鍙缃敞鍐屾暟閲忥紙涓嶅～榛樿 `100`锛?
- 鍙缃苟鍙戯紙榛樿 `10`锛?
- 娉ㄥ唽鍓嶄細鑷姩鍚姩鏈湴 Turnstile Solver锛堥粯璁?5 绾跨▼锛夛紝娉ㄥ唽缁撴潫鍚庤嚜鍔ㄥ叧闂?
- 娉ㄥ唽鎴愬姛鍚庝細鑷姩鎵ц锛氬悓鎰忕敤鎴峰崗璁紙TOS锛? 璁剧疆骞撮緞 + 寮€鍚?NSFW
  - 鑻?TOS / 骞撮緞 / NSFW 浠讳竴姝ラ澶辫触锛屼細鍒ゅ畾璇ユ娉ㄥ唽澶辫触骞跺湪鍓嶇鏄剧ず閿欒鍘熷洜

鑷姩娉ㄥ唽鍓嶇疆閰嶇疆锛堝湪銆岄厤缃鐞嗐€?> `register.*`锛夛細
- `register.worker_domain` / `register.email_domain` / `register.admin_password`锛氫复鏃堕偖绠?Worker 閰嶇疆
- `register.solver_url` / `register.solver_browser_type` / `register.solver_threads`锛氭湰鍦?Turnstile Solver 閰嶇疆
- 鍙€夛細`register.yescaptcha_key`锛堥厤缃悗浼樺厛璧?YesCaptcha锛屾棤闇€鏈湴 solver锛?

鍗囩骇鍏煎锛?
- 鏈湴閮ㄧ讲鍗囩骇鍚庝細鑷姩瀵广€屾棫 Token銆嶅仛涓€娆?TOS + 璁剧疆骞撮緞 + NSFW锛堝苟鍙?10锛宐est-effort锛屼粎鎵ц涓€娆★紝閬垮厤閲嶅鍒凤級銆?

### 鐜鍙橀噺

> 閰嶇疆 `.env` 鏂囦欢

| 鍙橀噺鍚?                 | 璇存槑                                                | 榛樿鍊?     | 绀轰緥                                                |
| :---------------------- | :-------------------------------------------------- | :---------- | :-------------------------------------------------- |
| `LOG_LEVEL`           | 鏃ュ織绾у埆                                            | `INFO`    | `DEBUG`                                           |
| `SERVER_HOST`         | 鏈嶅姟鐩戝惉鍦板潃                                        | `0.0.0.0` | `0.0.0.0`                                         |
| `SERVER_PORT`         | 鏈嶅姟绔彛                                            | `8000`    | `8000`                                            |
| `SERVER_WORKERS`      | Uvicorn worker 鏁伴噺                                 | `1`       | `2`                                               |
| `SERVER_STORAGE_TYPE` | 瀛樺偍绫诲瀷锛坄local`/`redis`/`mysql`/`pgsql`锛?| `local`   | `pgsql`                                           |
| `SERVER_STORAGE_URL`  | 瀛樺偍杩炴帴涓诧紙local 鏃跺彲涓虹┖锛?                       | `""`      | `postgresql+asyncpg://user:password@host:5432/db` |

### 閰嶇疆鏂囦欢涓庡崌绾ц縼绉?

- 閰嶇疆鏂囦欢锛歚data/config.toml`锛堥娆″惎鍔ㄤ細鍩轰簬 `config.defaults.toml` 鑷姩鐢熸垚锛涚鐞嗛潰鏉夸篃鍙洿鎺ヤ慨鏀癸級
- Token 鏁版嵁锛歚data/token.json`
- 鍗囩骇鏃惰嚜鍔ㄥ吋瀹硅縼绉伙紙鏈湴/Docker锛夛細
  - 鏃х増閰嶇疆锛氭娴嬪埌 `data/setting.toml` 鏃讹紝浼氭寜鈥滅己澶卞瓧娈?浠嶄负榛樿鍊尖€濈殑绛栫暐鍚堝苟鍒版柊閰嶇疆
  - 鏃х増缂撳瓨鐩綍锛歚data/temp/{image,video}` -> `data/tmp/{image,video}`
  - 鏃ц处鍙蜂竴娆℃€т慨澶嶏紙best-effort锛夛細鍗囩骇鍚庝細瀵圭幇鏈?Token 鑷姩鎵ц涓€娆°€屽悓鎰忕敤鎴峰崗璁?+ 璁剧疆骞撮緞 + 寮€鍚?NSFW銆嶏紙骞跺彂 10锛?


### 鍙敤娆℃暟

- Basic 璐﹀彿锛?0 娆?/ 20h
- Super 璐﹀彿锛氭棤璐﹀彿锛屼綔鑰呮湭娴嬭瘯

### 鍙敤妯″瀷

| 妯″瀷鍚?                    | 璁℃ | 鍙敤璐﹀彿    | 瀵硅瘽鍔熻兘 | 鍥惧儚鍔熻兘 | 瑙嗛鍔熻兘 |
| :------------------------- | :--: | :---------- | :------: | :------: | :------: |
| `grok-3`                 |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-3-mini`            |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-3-thinking`        |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4`                 |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4-mini`            |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4-thinking`        |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4-heavy`           |  4  | Super       |   鏀寔   |   鏀寔   |    -    |
| `grok-4.1-mini`          |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4.1-fast`          |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4.1-expert`        |  4  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4.1-thinking`      |  4  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-4.20-beta`         |  1  | Basic/Super |   鏀寔   |   鏀寔   |    -    |
| `grok-imagine-1.0`       |  -  | Basic/Super |    -    |   鏀寔   |    -    |
| `grok-imagine-1.0-edit`  |  -  | Basic/Super |    -    |   鏀寔   |    -    |
| `grok-imagine-1.0-video` |  -  | Basic/Super |    -    |    -    |   鏀寔   |

<br>

## 鎺ュ彛璇存槑

### `POST /v1/chat/completions`

> 閫氱敤鎺ュ彛锛屾敮鎸佸璇濊亰澶┿€佸浘鍍忕敓鎴愩€佸浘鍍忕紪杈戙€佽棰戠敓鎴愩€佽棰戣秴鍒?

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROK2API_API_KEY" \
  -d '{
    "model": "grok-4",
    "messages": [{"role":"user","content":"浣犲ソ"}]
  }'
```

<details>
<summary>鏀寔鐨勮姹傚弬鏁?/summary>

<br>

| 瀛楁                 | 绫诲瀷    | 璇存槑                           | 鍙敤鍙傛暟                                           |
| :------------------- | :------ | :----------------------------- | :------------------------------------------------- |
| `model`            | string  | 妯″瀷鍚嶇О                       | -                                                  |
| `messages`         | array   | 娑堟伅鍒楄〃                       | `developer`, `system`, `user`, `assistant` |
| `stream`           | boolean | 鏄惁寮€鍚祦寮忚緭鍑?              | `true`, `false`                                |
| `thinking`         | string  | 鎬濈淮閾炬ā寮?                    | `enabled`, `disabled`, `null`                |
| `video_config`     | object  | **瑙嗛妯″瀷涓撶敤閰嶇疆瀵硅薄** | -                                                  |
| 鈹斺攢`aspect_ratio` | string  | 瑙嗛瀹介珮姣?                    | `16:9`, `9:16`, `1:1`, `2:3`, `3:2`      |
| 鈹斺攢`video_length` | integer | 瑙嗛鏃堕暱 (绉?                  | `5` - `15`                                     |
| 鈹斺攢`resolution`   | string  | 鍒嗚鲸鐜?                        | `SD`, `HD`                                     |
| 鈹斺攢`preset`       | string  | 椋庢牸棰勮                       | `fun`, `normal`, `spicy`                     |

娉細闄や笂杩板鐨勫叾浠栧弬鏁板皢鑷姩涓㈠純骞跺拷鐣?

<br>

</details>

### `POST /v1/images/generations`

> 鍥惧儚鐢熸垚鎺ュ彛

```bash
curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROK2API_API_KEY" \
  -d '{
    "model": "grok-imagine-1.0",
    "prompt": "涓€鍙湪澶┖婕傛诞鐨勭尗",
    "n": 1
  }'
```

<details>
<summary>鏀寔鐨勮姹傚弬鏁?/summary>

<br>

| 瀛楁 | 绫诲瀷 | 璇存槑 | 鍙敤鍙傛暟 |
| :--- | :--- | :--- | :--- |
| `model` | string | 鍥惧儚妯″瀷鍚?| `grok-imagine-1.0` |
| `prompt` | string | 鍥惧儚鎻忚堪鎻愮ず璇?| - |
| `n` | integer | 鐢熸垚鏁伴噺 | `1` - `10`锛堟祦寮忎粎 `1` 鎴?`2`锛?|
| `stream` | boolean | 鏄惁寮€鍚祦寮忚緭鍑?| `true`, `false` |
| `size` | string | 鍥剧墖灏哄/姣斾緥 | `1024x1024`銆乣1280x720`銆乣720x1280`銆乣1792x1024`銆乣1024x1792`銆乣16:9`銆乣9:16`銆乣1:1`銆乣2:3`銆乣3:2` |
| `concurrency` | integer | 鏂版柟寮忓苟鍙戞暟 | `1` - `3`锛堜粎鏂扮敓鍥炬柟寮忕敓鏁堬級 |
| `response_format` | string | 鍥剧墖杩斿洖鏍煎紡 | `url`, `base64`, `b64_json`锛堥粯璁よ窡闅?`app.image_format`锛?|

娉細
- `grok.image_generation_method=imagine_ws_experimental` 鏀寔 `single`锛堝崟娆★級涓?`continuous`锛堟寔缁級涓ょ妯″紡銆?
- `size` 鍦ㄦ柊鏂瑰紡涓嬩細鏄犲皠涓烘瘮渚嬶細`1024x576/1280x720/1536x864 -> 16:9`锛宍576x1024/720x1280/864x1536 -> 9:16`锛宍1024x1024/512x512 -> 1:1`锛宍1024x1536/1024x1792/512x768/768x1024 -> 2:3`锛宍1536x1024/1792x1024/768x512/1024x768 -> 3:2`锛涘叾浠栧€奸粯璁?`2:3`銆?
- 闄や笂杩板鐨勫叾浠栧弬鏁板皢鑷姩涓㈠純骞跺拷鐣ャ€?

<br>

</details>

<br>

### `POST /v1/images/generations/nsfw`

> NSFW 涓撶敤鍥惧儚鐢熸垚鎺ュ彛锛堝己鍒朵娇鐢?imagine websocket锛屽苟鍦ㄥ崟娆¤姹傚唴瀵瑰涓?Token 鍋氬け璐ュ洖閫€锛?
```bash
curl http://localhost:8000/v1/images/generations/nsfw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROK2API_API_KEY" \
  -d '{
    "model": "grok-imagine-1.0",
    "prompt": "缁樺埗涓€寮犲搴楅鏍肩殑浜哄儚娴锋姤",
    "n": 1,
    "response_format": "url"
  }'
```

<details>
<summary>鏀寔鐨勮姹傚弬鏁?/summary>

<br>

| 瀛楁 | 绫诲瀷 | 璇存槑 | 鍙敤鍙傛暟 |
| :--- | :--- | :--- | :--- |
| `model` | string | 鍥惧儚妯″瀷鍚?| `grok-imagine-1.0` |
| `prompt` | string | 鍥惧儚鎻忚堪鎻愮ず璇?| - |
| `n` | integer | 鐢熸垚鏁伴噺 | `1` - `4`锛堟祦寮忎粎 `1` 鎴?`2`锛?|
| `stream` | boolean | 鏄惁寮€鍚祦寮忚緭鍑?| `true`, `false` |
| `size` | string | 鍥剧墖灏哄/姣斾緥 | 鍚?`/v1/images/generations` |
| `concurrency` | integer | 鏂版柟寮忓苟鍙戞暟 | `1` - `3`锛堜粎闈炴祦寮忕敓鏁堬級 |
| `response_format` | string | 鍥剧墖杩斿洖鏍煎紡 | `url`, `base64`, `b64_json`锛堥粯璁よ窡闅?`app.image_format`锛?|

璇存槑锛?- 璇ユ帴鍙?**涓嶄緷璧?* `grok.image_generation_method`锛屼細寮哄埗璧?`imagine_ws_experimental`銆?- 褰撳綋鍓嶉€夋嫨鐨?Token 鍑哄浘澶辫触鏃讹紝浼氬湪鏈璇锋眰鍐呰嚜鍔ㄥ垏鎹㈠埌鍏朵粬鍙敤 Token 閲嶈瘯锛坆est-effort锛夈€?- 褰撳墠瀹炵幇浣嶄簬 `python-fastapi`锛堟湰鍦?Docker锛夛紱Cloudflare Workers/Pages 渚у闇€鍚屽悕鎺ュ彛鍙啀琛ラ綈銆?
<br>

</details>

<br>

### `GET /v1/images/method`

> 杩斿洖褰撳墠鐢熷浘鍚庣鏂瑰紡锛坄/chat` 涓?`/admin/chat` 鐢ㄤ簬鍒ゆ柇鏄惁鍚敤鈥滄柊鐢熷浘鐎戝竷娴?+ 瀹介珮姣?+ 骞跺彂鈥濓級

```bash
curl http://localhost:8000/v1/images/method \
  -H "Authorization: Bearer $GROK2API_API_KEY"
```

杩斿洖绀轰緥锛?
```json
{ "image_generation_method": "legacy" }
```

- 鍙€夊€硷細`legacy`銆乣imagine_ws_experimental`
- Cloudflare / Docker / 鏈湴 涓夌閮ㄧ讲鍧囦繚鎸佸悓涓€鎺ュ彛璇箟

<br>

#### `imagine_ws_experimental` (`/chat` + `/admin/chat`)

- In experimental mode, the image panel is replaced and supports two run modes: `single` and `continuous`.
- `single` keeps using `POST /v1/images/generations` and remains response-compatible.
- `continuous` uses WebSocket: `/api/v1/admin/imagine/ws?api_key=<API_KEY>`.
- WS commands: `start` / `stop` / `ping`.
- WS events: `status` / `image` / `error` / `pong`.
- Continuous payload includes `b64_json`, `sequence`, `elapsed_ms`, `aspect_ratio`, `run_id`.

### `POST /v1/images/edits`

> 鍥惧儚缂栬緫鎺ュ彛锛坄multipart/form-data`锛?

```bash
curl http://localhost:8000/v1/images/edits \
  -H "Authorization: Bearer $GROK2API_API_KEY" \
  -F "model=grok-imagine-1.0-edit" \
  -F "prompt=缁欒繖鍙尗鍔犱竴鍓お闃抽暅" \
  -F "image=@./cat.png" \
  -F "n=1" \
  -F "response_format=url"
```

<details>
<summary>鏀寔鐨勮姹傚弬鏁?/summary>

<br>

| 瀛楁 | 绫诲瀷 | 璇存槑 | 鍙敤鍙傛暟 |
| :--- | :--- | :--- | :--- |
| `model` | string | 鍥惧儚妯″瀷鍚?| `grok-imagine-1.0-edit` |
| `prompt` | string | 缂栬緫鎻愮ず璇?| - |
| `image` | file[] | 寰呯紪杈戝浘鐗囷紙鏈€澶?16 寮狅級 | `png`, `jpg`, `jpeg`, `webp` |
| `n` | integer | 鐢熸垚鏁伴噺 | `1` - `10`锛堟祦寮忎粎 `1` 鎴?`2`锛?|
| `stream` | boolean | 鏄惁寮€鍚祦寮忚緭鍑?| `true`, `false` |
| `response_format` | string | 鍥剧墖杩斿洖鏍煎紡 | `url`, `base64`, `b64_json`锛堥粯璁よ窡闅?`app.image_format`锛?|

娉細`mask` 鍙傛暟褰撳墠鏈疄鐜帮紝浼氳蹇界暐銆?

<br>

</details>

<br>

### 鍚庡彴绠＄悊 API 鍏煎鍙樻洿锛團astAPI + Workers锛?

1. `GET /api/v1/admin/tokens`锛堝閲忓吋瀹癸紝淇濈暀鏃у瓧娈碉級鏂板锛?
   - `token_type`
   - `quota_known`
   - `heavy_quota`
   - `heavy_quota_known`
2. `POST /api/v1/admin/keys/update`锛?
   - 褰?key 涓嶅瓨鍦ㄦ椂杩斿洖 `404`锛堟鍓嶉儴鍒嗗疄鐜板彲鑳借繑鍥炴垚鍔燂級銆?
3. 棰濆害璇箟琛ュ厖锛?
   - `quota_known = false` 琛ㄧず棰濆害鏈煡锛堜緥濡?`remaining_queries = -1` 鍦烘櫙锛夛紝涓嶅簲鐩存帴鍒ゅ畾涓衡€滈搴︾敤灏解€濄€?

## 鍙傛暟閰嶇疆

閰嶇疆鏂囦欢锛歚data/config.toml`

> [!NOTE]
> 鐢熶骇鐜鎴栧弽鍚戜唬鐞嗛儴缃叉椂锛岃纭繚 `app.app_url` 閰嶇疆涓哄澶栧彲璁块棶鐨勫畬鏁?URL锛?
> 鍚﹀垯鍙兘鍑虹幇鏂囦欢璁块棶閾炬帴涓嶆纭垨 403 绛夐棶棰樸€?

### 鍗囩骇杩佺Щ锛堜笉涓㈡暟鎹級

褰撲綘浠庢棫鐗堟湰鍗囩骇鍒板綋鍓嶇増鏈椂锛岀▼搴忎細鍦ㄥ惎鍔ㄦ椂鑷姩鍏煎骞惰鍙栨棫鏁版嵁锛?

- 鏃ч厤缃細鑻ュ瓨鍦?`data/setting.toml`锛屼細鑷姩杩佺Щ/鍚堝苟鍒?`data/config.toml`锛堜粎瑕嗙洊鈥滅己澶遍」鈥濇垨鈥滀粛涓洪粯璁ゅ€尖€濈殑瀛楁锛夈€?
- 鏃х紦瀛樼洰褰曪細鏃х増 `data/temp/{image,video}` 浼氳嚜鍔ㄨ縼绉诲埌鏂扮増 `data/tmp/{image,video}`锛屾湭鍒版竻鐞嗘椂闂寸殑缂撳瓨鏂囦欢涓嶄細涓㈠け銆?
- Docker 閮ㄧ讲锛氬姟蹇呮寔涔呭寲鎸傝浇 `./data:/app/data`锛堜互鍙?`./logs:/app/logs`锛夛紝鍚﹀垯瀹瑰櫒鏇存柊/閲嶅缓浼氫涪澶辨湰鍦版暟鎹€?

| 妯″潡                  | 瀛楁                         | 閰嶇疆鍚?      | 璇存槑                                                 | 榛樿鍊?                                                   |
| :-------------------- | :--------------------------- | :----------- | :--------------------------------------------------- | :-------------------------------------------------------- |
| **app**         | `app_url`                  | 搴旂敤鍦板潃     | 褰撳墠 Grok2API 鏈嶅姟鐨勫閮ㄨ闂?URL锛岀敤浜庢枃浠堕摼鎺ヨ闂€?| `http://127.0.0.1:8000`                                 |
|                       | `admin_username`           | 鍚庡彴璐﹀彿     | 鐧诲綍 Grok2API 鏈嶅姟绠＄悊鍚庡彴鐨勭敤鎴峰悕銆?                | `admin`                                                 |
|                       | `app_key`                  | 鍚庡彴瀵嗙爜     | 鐧诲綍 Grok2API 鏈嶅姟绠＄悊鍚庡彴鐨勫瘑鐮侊紝璇峰Ε鍠勪繚绠°€?      | `admin`                                                 |
|                       | `api_key`                  | API 瀵嗛挜     | 璋冪敤 Grok2API 鏈嶅姟鎵€闇€鐨?Bearer Token锛岃濡ュ杽淇濈銆? | `""`                                                    |
|                       | `image_format`             | 鍥剧墖鏍煎紡     | 鐢熸垚鐨勫浘鐗囨牸寮忥紙url / base64 / b64_json锛夈€?         | `url`                                                   |
|                       | `video_format`             | 瑙嗛鏍煎紡     | 鐢熸垚鐨勮棰戞牸寮忥紙浠呮敮鎸?url锛夈€?                      | `url`                                                   |
| **grok**        | `temporary`                | 涓存椂瀵硅瘽     | 鏄惁鍚敤涓存椂瀵硅瘽妯″紡銆?                              | `true`                                                  |
|                       | `stream`                   | 娴佸紡鍝嶅簲     | 鏄惁榛樿鍚敤娴佸紡杈撳嚭銆?                              | `true`                                                  |
|                       | `thinking`                 | 鎬濈淮閾?      | 鏄惁鍚敤妯″瀷鎬濈淮閾捐緭鍑恒€?                            | `true`                                                  |
|                       | `dynamic_statsig`          | 鍔ㄦ€佹寚绾?    | 鏄惁鍚敤鍔ㄦ€佺敓鎴?Statsig 鍊笺€?                       | `true`                                                  |
|                       | `filter_tags`              | 杩囨护鏍囩     | 鑷姩杩囨护 Grok 鍝嶅簲涓殑鐗规畩鏍囩銆?                    | `["xaiartifact", "xai:tool_usage_card", "grok:render"]` |
|                       | `video_poster_preview`     | 瑙嗛娴锋姤棰勮 | 灏嗚繑鍥炲唴瀹逛腑鐨?`<video>` 鏍囩鏇挎崲涓哄彲鐐瑰嚮鐨?Poster 棰勮鍥俱€?| `false`                                                 |
|                       | `timeout`                  | 瓒呮椂鏃堕棿     | 璇锋眰 Grok 鏈嶅姟鐨勮秴鏃舵椂闂达紙绉掞級銆?                    | `120`                                                   |
|                       | `base_proxy_url`           | 鍩虹浠ｇ悊 URL | 浠ｇ悊璇锋眰鍒?Grok 瀹樼綉鐨勫熀纭€鏈嶅姟鍦板潃銆?                | `""`                                                    |
|                       | `asset_proxy_url`          | 璧勬簮浠ｇ悊 URL | 浠ｇ悊璇锋眰鍒?Grok 瀹樼綉鐨勯潤鎬佽祫婧愶紙鍥剧墖/瑙嗛锛夊湴鍧€銆?   | `""`                                                    |
|                       | `cf_clearance`             | CF Clearance | Cloudflare 楠岃瘉 Cookie锛岀敤浜庨獙璇?Cloudflare 鐨勯獙璇併€?| `""`                                                    |
|                       | `wreq_emulation_nsfw`      | NSFW 鎸囩汗妯℃澘 | NSFW 寮€鍚摼璺娇鐢ㄧ殑涓婃父娴忚鍣ㄦ寚绾癸紙`curl_cffi` 鐨?`impersonate` 鍊硷級銆傜暀绌鸿〃绀轰娇鐢ㄨ皟鐢ㄦ柟浼犲叆/榛樿鍊笺€?| `""`                                                    |
|                       | `max_retry`                | 鏈€澶ч噸璇?    | 璇锋眰 Grok 鏈嶅姟澶辫触鏃剁殑鏈€澶ч噸璇曟鏁般€?                | `3`                                                     |
|                       | `retry_status_codes`       | 閲嶈瘯鐘舵€佺爜   | 瑙﹀彂閲嶈瘯鐨?HTTP 鐘舵€佺爜鍒楄〃銆?                        | `[401, 429, 403]`                                       |
|                       | `image_generation_method`  | 鐢熷浘璋冪敤鏂瑰紡 | 鐢熷浘璋冪敤鏂瑰紡锛坄legacy` 鏃ф柟娉曪紱`imagine_ws_experimental` 鏂版柟娉曪紝瀹為獙鎬э級銆?| `legacy`                                                |
| **token**       | `auto_refresh`             | 鑷姩鍒锋柊     | 鏄惁寮€鍚?Token 鑷姩鍒锋柊鏈哄埗銆?                       | `true`                                                  |
|                       | `refresh_interval_hours`   | 鍒锋柊闂撮殧     | Token 鍒锋柊鐨勬椂闂撮棿闅旓紙灏忔椂锛夈€?                      | `8`                                                     |
|                       | `fail_threshold`           | 澶辫触闃堝€?    | 鍗曚釜 Token 杩炵画澶辫触澶氬皯娆″悗琚爣璁颁负涓嶅彲鐢ㄣ€?         | `5`                                                     |
|                       | `save_delay_ms`            | 淇濆瓨寤惰繜     | Token 鍙樻洿鍚堝苟鍐欏叆鐨勫欢杩燂紙姣锛夈€?                  | `500`                                                   |
|                       | `reload_interval_sec`      | 涓€鑷存€у埛鏂?  | 澶?worker 鍦烘櫙涓?Token 鐘舵€佸埛鏂伴棿闅旓紙绉掞級銆?         | `30`                                                    |
|                       | `nsfw_refresh_concurrency` | NSFW 鍒锋柊骞跺彂 | 鍚屾剰鍗忚/骞撮緞/NSFW 鍒锋柊鐨勯粯璁ゅ苟鍙戞暟銆?               | `10`                                                    |
|                       | `nsfw_refresh_retries`     | NSFW 鍒锋柊閲嶈瘯 | 鍒锋柊澶辫触鍚庣殑棰濆閲嶈瘯娆℃暟锛堜笉鍚娆★級銆?              | `3`                                                     |
| **cache**       | `enable_auto_clean`        | 鑷姩娓呯悊     | 鏄惁鍚敤缂撳瓨鑷姩娓呯悊锛屽紑鍚悗鎸変笂闄愯嚜鍔ㄥ洖鏀躲€?        | `true`                                                  |
|                       | `limit_mb`                 | 娓呯悊闃堝€?    | 缂撳瓨澶у皬闃堝€硷紙MB锛夛紝瓒呰繃闃堝€间細瑙﹀彂娓呯悊銆?            | `1024`                                                  |
| **performance** | `assets_max_concurrent`    | 璧勪骇骞跺彂涓婇檺 | 璧勬簮涓婁紶/涓嬭浇/鍒楄〃鐨勫苟鍙戜笂闄愩€傛帹鑽?25銆?             | `25`                                                    |
|                       | `media_max_concurrent`     | 濯掍綋骞跺彂涓婇檺 | 瑙嗛/濯掍綋鐢熸垚璇锋眰鐨勫苟鍙戜笂闄愩€傛帹鑽?50銆?              | `50`                                                    |
|                       | `usage_max_concurrent`     | 鐢ㄩ噺骞跺彂涓婇檺 | 鐢ㄩ噺鏌ヨ璇锋眰鐨勫苟鍙戜笂闄愩€傛帹鑽?25銆?                   | `25`                                                    |
|                       | `assets_delete_batch_size` | 璧勪骇娓呯悊鎵归噺 | 鍦ㄧ嚎璧勪骇鍒犻櫎鍗曟壒骞跺彂鏁伴噺銆傛帹鑽?10銆?                 | `10`                                                    |
|                       | `admin_assets_batch_size`  | 绠＄悊绔壒閲?  | 绠＄悊绔湪绾胯祫浜х粺璁?娓呯悊鎵归噺骞跺彂鏁伴噺銆傛帹鑽?10銆?      | `10`                                                    |

<br>

## 鏈淇

- 淇 Token 椤?`refreshStatus` 渚濊禆鍏ㄥ眬 `event` 鐨勯棶棰橈紝鏀逛负鏄惧紡浼犲叆鎸夐挳寮曠敤锛岄伩鍏嶄笉鍚岃繍琛岀幆澧冧笅鎸夐挳鐘舵€佸紓甯搞€?
- 鏂板 Token 缁熶竴褰掍竴鍖栵紙`normalizeSsoToken`锛夛紝淇 `sso=` 鍓嶇紑瀵艰嚧鐨勫幓閲嶃€佸鍏ャ€佹壒閲忛€夋嫨涓嶄竴鑷撮棶棰樸€?
- 淇 API Key 鏇存柊鎺ュ彛鈥渒ey 涓嶅瓨鍦ㄤ粛杩斿洖鎴愬姛鈥濋棶棰橈紝缁熶竴涓?`404`銆?
- 浼樺寲 Token/API Key 椤甸潰閿欒鎻愮ず锛屼紭鍏堝睍绀哄悗绔叿浣撻敊璇紙`detail/error/message`锛夈€?

## 鏈鏇存柊琛ュ厖锛堟湰鍦?Docker锛?

- 鏂板锛氬鍏?鎵嬪姩娣诲姞/澶栭儴鍐欏叆鏂板 Token 鍚庯紝浼氬湪鍚庡彴鑷姩鎵ц `鍚屾剰鍗忚 + 璁剧疆骞撮緞 + 寮€鍚?NSFW`銆?
- 鏂板锛歍oken 绠＄悊椤靛鍔犮€屼竴閿埛鏂?NSFW銆嶆寜閽紝榛樿瀵瑰叏閮?Token 鎵ц涓婅堪娴佺▼銆?
- 鏂板锛氭壒閲忓埛鏂伴粯璁ゅ苟鍙?`10`锛屽け璐ュ悗棰濆閲嶈瘯 `3` 娆★紱閲嶈瘯鑰楀敖鑷姩鏍囪涓哄け鏁堛€?- 鏂板閰嶇疆锛?  - `token.nsfw_refresh_concurrency`锛堥粯璁?`10`锛?  - `token.nsfw_refresh_retries`锛堥粯璁?`3`锛?- 鏂板锛歚POST /v1/images/generations/nsfw`锛圢SFW 涓撶敤鐢熷浘锛屽己鍒?imagine websocket + Token 澶辫触鍥為€€锛宍n<=4`锛?- 鏂板閰嶇疆锛歚grok.wreq_emulation_nsfw`锛堝彲閫夛紝鐢ㄤ簬 NSFW 寮€鍚摼璺殑 `impersonate` 鎸囩汗妯℃澘锛?- 璇存槑锛氳鍔熻兘浠呭湪 `python-fastapi`锛堟湰鍦?Docker锛夊紑鏀撅紱`cloudflare-workers` 渚т笉灞曠ず璇ユ寜閽€?
## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TQZHR/grok2api&type=Timeline)](https://star-history.com/#TQZHR/grok2api&Timeline)



