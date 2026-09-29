import React from 'react';
import AssistantChatCore from './AssistantChatCore';

export default function AssistantWidget({
  isEmbedded = false,
  mode = 'fullpage',
  onMaximize,
  onClose,
  className = '',
}) {
  return (
    <AssistantChatCore
      mode={isEmbedded ? 'floating' : mode}
      onMaximize={onMaximize}
      onClose={onClose}
      className={className}
    />
  );
}

export { AssistantChatCore };
