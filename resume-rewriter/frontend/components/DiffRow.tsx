import React from "react";

type Props = {
  indexHint: number | null;
  before: string;
  after: string;
  accepted: boolean;
  onAccept: () => void;
  onReject: () => void;
};

export default function DiffRow({ indexHint, before, after, accepted, onAccept, onReject }: Props) {
  return (
    <div style={{
      border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, marginBottom: 10,
      background: accepted ? "#eefbea" : "white"
    }}>
      <div style={{display: "flex", justifyContent: "space-between", marginBottom: 6}}>
        <div style={{fontWeight: 600}}>Bullet {indexHint !== null ? `#${indexHint}` : "?"}</div>
        <div style={{display: "flex", gap: 8}}>
          <button
            onClick={onAccept}
            style={{padding:"6px 10px", border:"1px solid #16a34a", borderRadius: 8, background:"#16a34a", color:"white"}}
          >Accept</button>
          <button
            onClick={onReject}
            style={{padding:"6px 10px", border:"1px solid #9ca3af", borderRadius: 8, background:"white"}}
          >Reject</button>
        </div>
      </div>
      <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap: 12}}>
        <div>
          <div style={{fontSize:12, color:"#6b7280"}}>Original</div>
          <div style={{whiteSpace:"pre-wrap"}}>{before}</div>
        </div>
        <div>
          <div style={{fontSize:12, color:"#6b7280"}}>Suggested</div>
          <div style={{whiteSpace:"pre-wrap"}}>{after}</div>
        </div>
      </div>
    </div>
  );
}


