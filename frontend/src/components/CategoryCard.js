import React from "react";
import { Link } from "react-router-dom";
import { ICONS_BY_KEY_MAP } from "./Icons";

export default function CategoryCard({ category, count }) {
  const Icon = ICONS_BY_KEY_MAP()[category.icon];

  return (
    <Link to={`/${category.key}`} className={`cat-card cat-card--${category.accent}`}>
      <div className="cat-card-accent" />
      <div className="cat-card-body">
        <div className="cat-card-icon">
          <Icon />
        </div>
        <h3 className="cat-card-title">{category.label}</h3>
        <p className="cat-card-desc">{category.description}</p>
      </div>
      <div className="cat-card-footer">
        <span className="cat-card-count">{count ?? "–"}</span>
        <span className="cat-card-count-label">signal{count === 1 ? "" : "s"}</span>
      </div>
    </Link>
  );
}
