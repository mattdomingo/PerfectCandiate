export type JsonPatchOp =
  | { op: "replace"; path: string; value: string };

export type Rewrite = {
  before: string;
  after: string;
  reason?: string;
};


