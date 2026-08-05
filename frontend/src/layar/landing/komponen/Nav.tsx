/** Nav fixed translucent — jadi solid+blur setelah scroll > 80px (setupNav
 *  desain asli, diterjemahkan ke useState + scroll listener pasif). */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function Nav() {
  const [solid, setSolid] = useState(false);

  useEffect(() => {
    const onScroll = () => setSolid(window.scrollY > 80);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`lp-nav ${solid ? "lp-nav--solid" : ""}`}>
      <div className="lp-nav__inner">
        <a href="#atas" className="lp-nav__brand">
          <img src="/logo-satu-muatan.svg" alt="Satu Muatan" />
        </a>
        <nav className="lp-nav__links">
          <a className="lp-nav__link" href="#masalah">
            Masalah
          </a>
          <a className="lp-nav__link" href="#cara-kerja">
            Cara Kerja
          </a>
          <a className="lp-nav__link" href="#perjalanan">
            Simulasi Perjalanan
          </a>
          <Link to="/masuk" className="lp-btn lp-btn--isi">
            Mulai
          </Link>
        </nav>
      </div>
    </header>
  );
}
