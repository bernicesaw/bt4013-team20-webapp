// signup.js - handles skills chips, suggestions, work experience entries, and salary formatting

// Format a number into locale string with 2 decimals
function formatCurrencyInput(el) {
  if (!el) return;
  let v = (el.value || '').toString().replace(/,/g, '');
  if (v === '') return;
  let num = parseFloat(v);
  if (isNaN(num)) return;
  el.value = num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function initSignupForm() {
  const skillsInput = document.getElementById('skills-input');
  const skillsList = document.getElementById('skills-list');
  const skillsHidden = document.getElementById('skills-hidden');
  const addWorkBtn = document.getElementById('add-work-exp');
  const workExpsContainer = document.getElementById('work-exps');
  const workExpsHidden = document.getElementById('work-experiences-hidden');
  const skillSuggestionsBox = document.getElementById('skill-suggestions');

  // lightweight skill suggestions; extend as needed
  const SKILL_SUGGESTIONS = [
    'Ada','Alibaba Cloud','Amazon Redshift','Amazon Web Services (Aws)','Android','Angular','Angular.Js','Angularjs',
    'Ansible','Apex','Apl','Apt','Arduino','Asp.Net','Asp.Net Core','Assembly','Astro','Aws','Axum','Bash/Shell',
    'Bash/Shell (All Shells)','Bash/Shell/Powershell','Bigquery','Blazor','Bun','C','C#','C++','Cargo','Cassandra',
    'Chocolatey','Clickhouse','Clojure','Cloud Firestore','Cloudflare','Cobol','Cockroachdb','Codeigniter',
    'Colocation','Composer','Cosmos Db','Couch Db','Couchbase','Couchdb','Crystal','Dart','Databricks','Databricks Sql',
    'Datadog','Datomic','Delphi','Deno','Digital Ocean','Digitalocean','Django','Docker','Drupal','Duckdb','Dynamodb',
    'Elasticsearch','Elixir','Elm','Erlang','Eventstoredb','Express','F#','Fastapi','Fastify','Firebase',
    'Firebase Realtime Database','Firebird','Flask','Flow','Fly.Io','Fortran','Gatsby','Gdscript','Gleam','Go',
    'Google Cloud','Google Cloud Platform','Gradle','Groovy','H2','Haskell','Heroku','Hetzner','Homebrew','Html/Css',
    'Htmx','Ibm Cloud','Ibm Cloud Or Watson','Ibm Db2','Influxdb','Ios','Java','Javascript','Jquery','Julia','Kotlin',
    'Kubernetes','Laravel','Linode','Linode, Now Akamai','Linux','Lisp','Lit','Lua','Macos','Make','Managed Hosting',
    'Mariadb','Matlab','Maven (Build Tool)','Micropython','Microsoft Access','Microsoft Azure','Microsoft Sql Server',
    'Mojo','Mongodb','Msbuild','Mysql','Neo4J','Nestjs','Netlify','New Relic','Next.Js','Nim','Ninja','Node.Js','Npm',
    'Nuget','Nuxt.Js','Objective-C','Ocaml','Openshift','Openstack','Oracle','Oracle Cloud Infrastructure',
    'Oracle Cloud Infrastructure (Oci)','Ovh','Pacman','Perl','Phoenix','Php','Pip','Play Framework','Pnpm','Pocketbase',
    'Podman','Poetry','Postgresql','Powershell','Presto','Prolog','Prometheus','Python','Pythonanywhere','Qwik','R',
    'Railway','Raku','Raspberry Pi','Ravendb','React','React.Js','Redis','Remix','Render','Ruby','Ruby On Rails','Rust',
    'Sas','Scala','Scaleway','Slack Apps And Integrations','Snowflake','Solid.Js','Solidity','Solr','Splunk','Spring',
    'Spring Boot','Sql','Sqlite','Strapi','Supabase','Svelte','Swift','Symfony','Terraform','Tidb','Typescript','Valkey',
    'Vba','Vercel','Visual Basic (.Net)','Vite','Vmware','Vue.Js','Vultr','Webpack','Windows','Wordpress','Yandex Cloud',
    'Yarn','Yii 2','Zephyr','Zig'
  ];

  let skills = [];
  let workExps = [];

  function renderSkillSuggestions(filter) {
    if (!skillSuggestionsBox) return;
    skillSuggestionsBox.innerHTML = '';
    const q = (filter||'').toLowerCase().trim();
    if (!q) return;
    const matches = SKILL_SUGGESTIONS.filter(s => s.toLowerCase().includes(q) && !skills.includes(s)).slice(0,8);
    matches.forEach(m => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-sm btn-outline-secondary me-1 mb-1';
      b.textContent = m;
      b.onclick = () => { addSkill(m); skillsInput.focus(); };
      skillSuggestionsBox.appendChild(b);
    });
  }

  function renderSkills() {
    if (!skillsList) return;
    skillsList.innerHTML = '';
    skills.forEach((s, idx) => {
      const span = document.createElement('span');
      span.className = 'badge bg-secondary text-white me-1';
      span.style.cursor = 'pointer';
      span.textContent = s + ' ×';
      span.onclick = () => {
        skills.splice(idx, 1);
        renderSkills();
      };
      skillsList.appendChild(span);
    });
    if (skillsHidden) skillsHidden.value = skills.join(', ');
  }

  function addSkill(val) {
    const v = (val || (skillsInput ? skillsInput.value : '') || '').trim();
    if (!v) return;
    if (skills.length >= 5) {
      alert('Max 5 skills allowed');
      if (skillsInput) skillsInput.value = '';
      return;
    }
    if (!skills.includes(v)) skills.push(v);
    if (skillsInput) skillsInput.value = '';
    renderSkills();
    renderSkillSuggestions('');
  }

  if (skillsInput) {
    skillsInput.addEventListener('input', (e) => renderSkillSuggestions(e.target.value));
    skillsInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(); } });
  }

  function addWorkExp() {
    if (!workExpsContainer) return;
    if (workExps.length >= 10) {
      alert('Max 10 work experiences allowed');
      return;
    }
    const idx = workExps.length;
    const container = document.createElement('div');
    container.className = 'work-exp border rounded p-2 mb-2';

    const jobTitle = document.createElement('input');
    jobTitle.placeholder = 'Job Title';
    jobTitle.className = 'form-control mb-2';
    jobTitle.setAttribute('list', 'jobtitles');
    jobTitle.required = true;

    // per-experience skills: an input, suggestions, and chips list
    const expSkillsInput = document.createElement('input');
    expSkillsInput.placeholder = 'Type a skill';
    expSkillsInput.className = 'form-control mb-2';
    expSkillsInput.required = true;
    const expSkillSuggestions = document.createElement('div');
    expSkillSuggestions.className = 'mb-2';
    const expSkillsList = document.createElement('div');
    expSkillsList.className = 'mb-2';
    const expSkillsHidden = document.createElement('input');
    expSkillsHidden.type = 'hidden';
    let expSkillsArr = [];

    function renderExpSkills() {
      expSkillsList.innerHTML = '';
      expSkillsArr.forEach((s, i) => {
        const span = document.createElement('span');
        span.className = 'badge bg-secondary text-white me-1';
        span.style.cursor = 'pointer';
        span.textContent = s + ' ×';
        span.onclick = () => { expSkillsArr.splice(i,1); renderExpSkills(); };
        expSkillsList.appendChild(span);
      });
      expSkillsHidden.value = expSkillsArr.join(', ');
    }

    function renderExpSkillSuggestions(q) {
      expSkillSuggestions.innerHTML = '';
      const ql = (q||'').toLowerCase().trim();
      if (!ql) return;
      const matches = SKILL_SUGGESTIONS.filter(s => s.toLowerCase().includes(ql) && !expSkillsArr.includes(s)).slice(0,6);
      matches.forEach(m => {
        const b = document.createElement('button');
        b.type = 'button'; b.className = 'btn btn-sm btn-outline-secondary me-1 mb-1'; b.textContent = m;
        b.onclick = () => { expSkillsArr.push(m); renderExpSkills(); expSkillsInput.focus(); };
        expSkillSuggestions.appendChild(b);
      });
    }

    expSkillsInput.addEventListener('input', (e)=> renderExpSkillSuggestions(e.target.value));
    expSkillsInput.addEventListener('keydown', (e)=> { if (e.key === 'Enter') { e.preventDefault(); const v=expSkillsInput.value.trim(); if(v && expSkillsArr.length<5 && !expSkillsArr.includes(v)){ expSkillsArr.push(v); expSkillsInput.value=''; renderExpSkills(); } } });

  const salary = document.createElement('input');
  salary.placeholder = 'Monthly Median Salary';
    salary.className = 'form-control me-2';
    salary.style.maxWidth = '260px';
  salary.required = true;

    const currency = document.createElement('select');
    currency.className = 'form-select w-auto';
    ['USD','SGD','EUR','GBP'].forEach(c => { const o = document.createElement('option'); o.value = c; o.text = c; currency.appendChild(o); });

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-sm btn-outline-danger ms-2';
    removeBtn.textContent = 'Remove';
    removeBtn.onclick = () => {
      workExps.splice(idx, 1);
      container.remove();
      updateWorkHidden();
    };

    salary.addEventListener('blur', () => formatCurrencyInput(salary));

  container.appendChild(jobTitle);
  // job title required indicator
  // skills input for this experience
  container.appendChild(expSkillsInput);
  container.appendChild(expSkillSuggestions);
  container.appendChild(expSkillsList);
  container.appendChild(expSkillsHidden);

    const row = document.createElement('div');
    row.className = 'd-flex align-items-center';
    row.appendChild(salary);
    row.appendChild(currency);
    row.appendChild(removeBtn);
    container.appendChild(row);

    workExpsContainer.appendChild(container);

  workExps.push({ jobTitle, salary, currency, expSkillsHidden });
    updateWorkHidden();
  }

  function updateWorkHidden() {
    if (!workExpsHidden) return;
    const arr = workExps.map(w => {
      // support per-experience skills hidden field if present
      let skillsArr = [];
      if (w.expSkillsHidden) {
        skillsArr = (w.expSkillsHidden.value || '').split(',').map(s => s.trim()).filter(Boolean);
      } else {
        skillsArr = (w.skillsField.value || '').split(',').map(s => s.trim()).filter(Boolean);
      }
      if (skillsArr.length > 5) skillsArr = skillsArr.slice(0,5);
      let salaryRaw = (w.salary.value||'').toString().replace(/,/g, '');
      let salaryNum = salaryRaw ? parseFloat(salaryRaw) : null;
      return {
        job_title: w.jobTitle.value || '',
        skills: skillsArr,
        median_salary: salaryNum,
        currency: w.currency.value || 'USD'
      };
    });
    workExpsHidden.value = JSON.stringify(arr);
  }

  if (addWorkBtn) addWorkBtn.addEventListener('click', addWorkExp);

  // update hidden fields on form submit
  const form = document.getElementById('signup-form');
  if (form) {
    form.addEventListener('submit', () => {
      if (skillsHidden) skillsHidden.value = skills.join(', ');
      updateWorkHidden();
    });
  }
}

// initialize behavior when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // format main median salary field if present
  const mainSalary = document.getElementById('id_median_salary');
  if (mainSalary) mainSalary.addEventListener('blur', () => formatCurrencyInput(mainSalary));
  // initialize dynamic form behaviors
  try { initSignupForm(); } catch (e) { console.warn('initSignupForm failed', e); }
});