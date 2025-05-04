const API_URL     = 'http://localhost:5000';
const LOGIN_URL   = `${API_URL}/api/login`;
const GAMES_URL   = `${API_URL}/api/games`;
const USERS_URL   = `${API_URL}/api/users`;
const PROFILE_URL = `${API_URL}/api/profile`;

function setToken(t){ localStorage.setItem('token', t) }
function getToken(){ return localStorage.getItem('token') }
function clearToken(){ localStorage.removeItem('token') }
function authHeaders(){ return {
  'Content-Type':'application/json',
  'Authorization':'Bearer '+getToken()
}}

const sections = [...document.querySelectorAll('section')];
function showSection(id){
  sections.forEach(s=> s.id===id ? s.style.display='block' : s.style.display='none');
}
function showNav(isAdmin){
  document.getElementById('nav-section').style.display='flex';
  document.getElementById('logout-btn').style.display='inline-block';
  document.getElementById('admin-nav').style.display = isAdmin ? 'block':'none';
  document.getElementById('user-nav').style.display  = isAdmin ? 'none':'block';
}
document.getElementById('logout-btn').onclick = ()=>{
  clearToken(); location.reload();
};

document.querySelectorAll('nav button').forEach(btn=>{
  btn.onclick = async ()=>{
    const sec = btn.dataset.show;
    showSection(sec);
    if(sec==='admin-games-section')  await loadAdminGames();
    if(sec==='admin-users-section')  await loadAdminUsers();
    if(sec==='profile-section')      await loadProfile();
    if(sec==='games-section')        await loadUserGames();
  }
});

// LOGIN
document.getElementById('login-form').onsubmit = async e=>{
  e.preventDefault();
  const email = e.target['login-email'].value;
  const password = e.target['login-password'].value;
  const res = await fetch(LOGIN_URL, {
    method:'POST', mode:'cors',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ email, password })
  });
  const j = await res.json();
  if(!res.ok) return alert(j.msg || 'Login failed');
  setToken(j.token);
  // decode is_admin
  const pl = j.token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/');
  const claims = JSON.parse(decodeURIComponent(atob(pl).split('').map(c=>'%'+('00'+c.charCodeAt(0).toString(16)).slice(-2)).join('')));
  if(claims.is_admin){
    showNav(true);
    await loadAdminGames();
    await loadAdminUsers();
    showSection('admin-games-section');
  } else {
    showNav(false);
    await loadProfile();
    await loadUserGames();
    showSection('profile-section');
  }
};

// ADMIN: load/create/delete games & users
async function loadAdminGames(){
  const c = document.getElementById('admin-games-list');
  c.innerHTML='<p class="placeholder">Loading games…</p>';
  const res = await fetch(GAMES_URL, {method:'GET',mode:'cors',headers:authHeaders()});
  const games = await res.json();
  if(!games.length) return c.innerHTML='<p class="placeholder">No games found</p>';
  c.innerHTML='';
  games.forEach(g=>{
    const id = g.id||g._id;
    const card = document.createElement('div');
    card.className='card';
    card.innerHTML=`
      <p><strong>${g.name}</strong><br>
         Genres: ${g.genres.join(', ')}<br>
         Avg Rating: ${g.rating??'-'}
      </p>
      <button class="btn btn-danger" data-action="delete-game" data-id="${id}">Delete Game</button>
    `;
    c.appendChild(card);
  });
}
document.getElementById('admin-games-list').addEventListener('click', async e=>{
  if(e.target.dataset.action==='delete-game'){
    if(!confirm('Delete this game?'))return;
    await fetch(`${GAMES_URL}/${e.target.dataset.id}`,{method:'DELETE',mode:'cors',headers:authHeaders()});
    alert('Game deleted');
    await loadAdminGames();
  }
});
document.getElementById('create-game-form').onsubmit=async e=>{
  e.preventDefault();
  const n=e.target['game-name'].value.trim(),
        g=e.target['game-genres'].value.split(',').map(s=>s.trim()).filter(s=>s),
        p=e.target['game-photo'].value,
        re=e.target['game-rating-enabled'].checked,
        ce=e.target['game-comment-enabled'].checked;
  const res=await fetch(GAMES_URL,{method:'POST',mode:'cors',headers:authHeaders(),body:JSON.stringify({name:n,genres:g,photo:p,rating_enabled:re,comment_enabled:ce})});
  const j=await res.json();
  if(!res.ok)return alert(j.msg);
  alert('Game created');
  e.target.reset();
  await loadAdminGames();
};
async function loadAdminUsers(){
  const c=document.getElementById('admin-users-list');
  c.innerHTML='<p class="placeholder">Loading users…</p>';
  const res=await fetch(USERS_URL,{method:'GET',mode:'cors',headers:authHeaders()});
  const us=await res.json();
  if(!us.length)return c.innerHTML='<p class="placeholder">No users found</p>';
  c.innerHTML='';
  us.forEach(u=>{
    const card=document.createElement('div');
    card.className='card';
    card.innerHTML=`<p><strong>${u.username}</strong> (${u.email}) ${u.is_admin?'<em>Admin</em>':''}</p>
      <button class="btn btn-danger" data-action="delete-user" data-id="${u._id}">Delete User</button>`;
    c.appendChild(card);
  });
}
document.getElementById('admin-users-list').addEventListener('click',async e=>{
  if(e.target.dataset.action==='delete-user'){
    if(!confirm('Delete this user?'))return;
    await fetch(`${USERS_URL}/${e.target.dataset.id}`,{method:'DELETE',mode:'cors',headers:authHeaders()});
    alert('User deleted');
    await loadAdminUsers();
  }
});
document.getElementById('create-user-form').onsubmit=async e=>{
  e.preventDefault();
  const un=e.target['user-username'].value.trim(),
        em=e.target['user-email'].value.trim(),
        pw=e.target['user-password'].value,
        ia=e.target['user-is-admin'].checked;
  const res=await fetch(USERS_URL,{method:'POST',mode:'cors',headers:authHeaders(),body:JSON.stringify({username:un,email:em,password:pw,is_admin:ia})});
  const j=await res.json();
  if(!res.ok)return alert(j.msg);
  alert('User created');
  e.target.reset();
  await loadAdminUsers();
};

// USER: Profile
async function loadProfile(){
  const card = document.getElementById('profile-card');
  card.innerHTML = '<p class="placeholder">Loading profile…</p>';
  const [profRes, gamesRes] = await Promise.all([
    fetch(PROFILE_URL, { method:'GET', mode:'cors', headers: authHeaders() }),
    fetch(GAMES_URL,   { method:'GET', mode:'cors', headers: authHeaders() })
  ]);
  const prof  = await profRes.json();
  const games = await gamesRes.json();
  const nameMap = {};
  games.forEach(g => {
    const id = g.id || g._id;
    nameMap[id] = g.name;
  });
  const played = prof.played || {};
  card.innerHTML = `
    <p><strong>Username:</strong> ${prof.username}</p>
    <p><strong>Email:</strong> ${prof.email}</p>
    <p><strong>Played:</strong></p>
    <ul>
      ${
        Object.entries(played).length
          ? Object.entries(played)
              .map(([gid, hrs]) => `<li>${nameMap[gid] || gid}: ${hrs} hr(s)</li>`)
              .join('')
          : '<li class="placeholder">No play history</li>'
      }
    </ul>
  `;
}

// USER: Games
async function loadUserGames(){
  const c=document.getElementById('user-games-list');
  c.innerHTML='<p class="placeholder">Loading games…</p>';
  const res=await fetch(GAMES_URL,{method:'GET',mode:'cors',headers:authHeaders()});
  const games=await res.json();
  if(!games.length)return c.innerHTML='<p class="placeholder">No games available</p>';
  c.innerHTML='';
  games.forEach(g=>{
    const id=g.id||g._id;
    const card=document.createElement('div');
    card.className='card';
    card.innerHTML=`
      <h4>${g.name}</h4>
      <p><strong>Genres:</strong> ${g.genres.join(', ')}</p>
      <p><strong>Avg Rating:</strong> ${g.rating ?? '-'} </p>
      <button class="btn btn-primary" data-action="play" data-id="${id}">Play +1 hr</button>
      <div>
        <input type="number" min="1" max="5" id="rate-${id}" placeholder="1–5"/>
        <button class="btn btn-primary" data-action="rate" data-id="${id}">Rate</button>
      </div>
      <div>
        <input type="text" id="cmt-${id}" placeholder="Comment"/>
        <button class="btn btn-primary" data-action="comment" data-id="${id}">Comment</button>
      </div>
      <div id="play-time-${id}"></div>
    `;
    c.appendChild(card);
  });
}

document.getElementById('user-games-list').addEventListener('click', async e=>{
  const id = e.target.dataset.id;
  if(e.target.dataset.action==='play'){
    const res=await fetch(`${GAMES_URL}/${id}/play`,{method:'POST',mode:'cors',headers:authHeaders()});
    const j=await res.json();
    document.getElementById(`play-time-${id}`).innerText=`Played: ${j.play_time_hours} hr(s)`;
    await loadProfile();
  }
  if(e.target.dataset.action==='rate'){
    const val=+document.getElementById(`rate-${id}`).value;
    const res=await fetch(`${GAMES_URL}/${id}/rate`,{
      method:'POST',mode:'cors',headers:authHeaders(),
      body:JSON.stringify({rating:val})
    });
    const j=await res.json();
    if(res.ok) alert(`New avg: ${j.avg_rating.average} (${j.avg_rating.count})`);
    else alert(j.msg);
    await loadUserGames();
  }
  if(e.target.dataset.action==='comment'){
    const txt=document.getElementById(`cmt-${id}`).value.trim();
    const res=await fetch(`${GAMES_URL}/${id}/comment`,{
      method:'POST',mode:'cors',headers:authHeaders(),
      body:JSON.stringify({comment:txt})
    });
    const j=await res.json();
    if(res.ok) alert('Comment added'); else alert(j.msg);
    await loadUserGames();
  }
});

// Start at login
window.onload = ()=> showSection('login-section');
