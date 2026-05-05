# Festival Playlist Web

페스티벌 포스터 이미지, CSV, 줄바꿈 텍스트에서 라인업을 만들고 검수한 뒤 아티스트별 YouTube 영상 후보를 검수하여 플레이리스트를 생성하는 MVP 웹앱입니다.

## Architecture

Frontend는 React + Vite 단일 페이지 앱입니다. 화면은 `Home -> Lineup Review -> Video Search Review -> Playlist Create` 순서로 이동하며, 요청 단위 선택 입력값은 브라우저 state에만 보관합니다. `localStorage`를 사용하지 않습니다.

Backend는 FastAPI stateless API입니다. DB를 쓰지 않고, CSV/텍스트 파싱은 요청 단위로 처리합니다. 포스터 이미지는 디스크에 저장하지 않고 업로드 스트림을 메모리에서 읽은 뒤 닫습니다. OpenAI API Key는 서버 환경변수 `OPENAI_API_KEY`에서 읽고 저장하지 않습니다.

YouTube OAuth 토큰은 `backend/app/services/token_store.py`의 프로세스 메모리에만 TTL로 보관합니다. 서버 재시작 시 토큰과 OAuth state는 모두 삭제됩니다.

## Project Structure

```text
festival-playlist-web/
  frontend/
    src/
      App.jsx
      api/client.js
      pages/
      components/
  backend/
    app/
      main.py
      routers/
      services/
      utils/
  README.md
```

## Google Cloud Console Setup

1. Google Cloud Console에서 새 프로젝트를 만들거나 기존 프로젝트를 선택합니다.
2. **APIs & Services -> Library**에서 **YouTube Data API v3**를 활성화합니다.
3. **APIs & Services -> Credentials**에서 OAuth consent screen을 구성합니다.
4. **Create Credentials -> OAuth client ID**를 선택합니다.
5. Application type은 **Web application**으로 선택합니다.
6. Authorized redirect URIs에 다음 값을 추가합니다.

```text
http://localhost:8000/api/youtube/callback
```

7. 생성된 `Client ID`, `Client Secret`을 `backend/.env`에 넣습니다.
8. YouTube 검색을 OAuth 전에 수행하려면 YouTube Data API용 API Key를 만들고 `YOUTUBE_API_KEY`에 넣습니다.

## Backend Run

```bash
cd festival-playlist-web/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

`backend/.env` 예시:

```bash
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
OPENAI_API_KEY=
OPENAI_VISION_MODEL=gpt-4.1-mini
YOUTUBE_API_KEY=
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
YOUTUBE_REDIRECT_URI=http://localhost:8000/api/youtube/callback
YOUTUBE_TOKEN_TTL_SECONDS=3600
YOUTUBE_STATE_TTL_SECONDS=600
```

## Frontend Run

```bash
cd festival-playlist-web/frontend
npm install
cp .env.example .env
npm run dev
```

기본 접속 주소:

```text
http://localhost:5173
```

## API Key Input

OpenAI API Key는 Backend `.env`의 `OPENAI_API_KEY`에 넣습니다. 프론트엔드는 OpenAI API Key를 입력받거나 저장하지 않습니다.

YouTube 검색 API Key는 Backend `.env`의 `YOUTUBE_API_KEY`에 넣습니다. 프론트엔드는 YouTube 검색 API Key를 입력받거나 저장하지 않습니다. 영상 검색은 승인된 아티스트마다 `official music video` 기준으로 최대 70개 후보를 가져오고, 제목이 같은 후보는 조회수가 가장 높은 영상만 남깁니다. 검수 화면에서는 아티스트 탭별로 조회수와 등록일을 보며 사용할 영상을 선택합니다.

## Data Retention Model

- DB 없음
- OpenAI API Key 저장 없음
- 업로드 이미지 영구 저장 없음
- CSV/텍스트 입력 영구 저장 없음
- YouTube OAuth 토큰은 서버 메모리에만 TTL 저장
- OAuth state도 서버 메모리에만 짧은 TTL 저장
- 서버 재시작 시 OAuth 세션 삭제

## API

### `POST /api/poster/extract`

OpenAI API Key는 Backend `.env`의 `OPENAI_API_KEY`를 사용합니다. 요청 단위로 다른 키를 써야 하는 경우에만 다음 header를 보낼 수 있습니다.

```text
Authorization: Bearer {OPENAI_API_KEY}
```

Form fields:

- `file`: poster image
- `image_url`: poster image URL
- `festival_name`: optional

`file` 또는 `image_url` 중 하나를 보내면 됩니다. `image_url`은 SSRF 방지를 위해 `http/https`만 허용하고 localhost/private IP 대역은 차단합니다. 원격 이미지는 메모리에서만 읽고 저장하지 않습니다.

### `POST /api/lineup/from-csv`

CSV columns:

```text
festival_name,date,day_label,artist_name,stage,start_time,approved
```

`artist_name`만 있어도 동작합니다. 부족한 필드는 `null`로 반환합니다.

### `POST /api/lineup/from-text`

Body:

```json
{
  "text": "Artist A\nArtist B"
}
```

### `POST /api/youtube/search`

Header optional:

```text
X-Session-Id: {YOUTUBE_OAUTH_SESSION_ID}
```

Body:

```json
{
  "festival_name": "Festival Name",
  "items": []
}
```

### `GET /api/youtube/auth-url`

OAuth URL과 임시 `session_id`를 반환합니다.

### `GET /api/youtube/callback`

Google OAuth callback입니다. 토큰은 메모리 TTL 저장소에만 저장됩니다.

### `GET /api/youtube/status?session_id=...`

OAuth 로그인 여부를 반환합니다.

### `POST /api/youtube/create-playlist`

Header:

```text
X-Session-Id: {YOUTUBE_OAUTH_SESSION_ID}
```

Body:

```json
{
  "playlist_name": "My Festival Playlist",
  "privacy": "private",
  "videos": []
}
```

## Lineup Schema

```json
{
  "date": "YYYY-MM-DD or null",
  "day_label": "DAY 1 or null",
  "artist_name": "string",
  "stage": "string or null",
  "start_time": "HH:mm or null",
  "source_text": "string",
  "confidence": 0.0,
  "approved": true,
  "source": "poster|csv|manual"
}
```

## YouTube Quota Notes

YouTube Data API v3는 quota를 사용합니다. 검색은 `search.list`, 영상 길이 확인은 `videos.list`, 플레이리스트 생성은 `playlists.insert`, 영상 추가는 `playlistItems.insert` quota를 사용합니다. 라인업이 많으면 검색 요청 수가 빠르게 늘 수 있으므로 MVP에서는 승인된 artist만 검색합니다.

## MVP Limitations

- 포스터 추출 품질은 이미지 해상도와 포스터 디자인에 영향을 받습니다.
- Shorts 판별은 제목/메타데이터와 60초 이하 duration 필터를 조합합니다.
- YouTube OAuth 세션은 브라우저 새로고침 또는 서버 재시작 후 이어지지 않을 수 있습니다.
- 동시 사용자별 영구 세션 관리는 의도적으로 포함하지 않았습니다.
