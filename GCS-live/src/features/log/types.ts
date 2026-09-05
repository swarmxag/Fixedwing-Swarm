export type LogItem = {
  id: number;
  timestamp: number;
  message: string;
  module: string;
  level: number;
  auxiliaryId: string;
};

export type FileItem = {
  time: number;
  message: string;
};
