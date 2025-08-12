import React from "react";

type Props = Readonly<{
  indexHint: number | null;
  before: string;
  after: string;
  accepted: boolean;
  onAccept: () => void;
  onReject: () => void;
}>;

export default function DiffRow({ indexHint, before, after, accepted, onAccept, onReject }: Props) {
  return (
    <div className={`diff-row ${accepted ? "accepted" : ""}`}>
      <div className="diff-row__top">
        <div className="chip">Bullet {indexHint !== null ? `#${indexHint}` : "?"}</div>
        <div className="row gap">
          <button onClick={onAccept} className="btn btn-success">Accept</button>
          <button onClick={onReject} className="btn">Reject</button>
        </div>
      </div>
      <div className="diff-grid">
        <div>
          <div className="muted tiny">Original</div>
          <div className="text-block">{before}</div>
        </div>
        <div>
          <div className="muted tiny">Suggested</div>
          <div className="text-block">{after}</div>
        </div>
      </div>
    </div>
  );
}


