document.write(`
<header class="site-header" id="site-header">
    <style>
      .site-header { position: relative; z-index: 9999 !important; }
      .dropdown { z-index: 10000 !important; }
    </style>
    <div class="header-top">
      <div class="container">
        <span>The open FHIR standard for end-to-end life sciences regulatory workflows</span>
        <div class="header-links">
          <a href="#">About</a>
          <a href="#">Contact</a>
          <a href="#">GitHub</a>
        </div>
      </div>
    </div>
    <nav class="main-nav">
      <div class="container nav-inner">
        <a href="index.html" class="logo">
          <div class="logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M4 6h16M4 12h10M4 18h13" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
              <circle cx="20" cy="18" r="3.5" fill="white" fill-opacity="0.9"/>
              <path d="M18.5 18l1 1 2.5-2" stroke="#0052CC" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="logo-text">
            <span class="logo-main">FHIR-LS</span>
            <span class="logo-sub">Life Sciences Catalogue</span>
          </div>
        </a>
        <ul class="nav-menu">
          <li><a href="index.html" class="nav-link">Home</a></li>
          <li class="has-dropdown">
            <a href="#" class="nav-link">Standards <span class="chevron">▾</span></a>
            <ul class="dropdown">
              <li><a href="standard-epi.html">ePI — Labelling</a></li>
              <li><a href="standard-idmp.html">IDMP — Product Identity</a></li>
              <li><a href="standard-pqi.html">PQI — CMC Quality</a></li>
              <li><a href="standard-apix.html">APIX — Information Exchange</a></li>
              <li><a href="standard-icsr.html">AER — Adverse Event Reporting</a></li>
              <li><a href="standard-hta.html">HTA — Health Technology Assessment</a></li>
              <li><a href="standard-rtq.html">RTQ — Regulatory Questions</a></li>
            </ul>
          </li>
          <li><a href="index.html#standards" class="nav-link">Catalogue</a></li>
          <li><a href="#" class="nav-link">Data Dictionary</a></li>
          <li><a href="adoption.html" class="nav-link">Adoption</a></li>
        </ul>
        <div class="nav-actions">
          <a href="index.html#standards" class="btn btn-primary">Browse Catalogue</a>
        </div>
      </div>
    </nav>
  </header>
`);