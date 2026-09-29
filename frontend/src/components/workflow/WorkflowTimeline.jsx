import React from 'react';
import AgenticWorkflowThread from './AgenticWorkflowThread';

/**
 * WorkflowTimeline
 * Canonical adapter rendering the unified AgenticWorkflowThread across the application.
 */
export const WorkflowTimeline = ({ className = '' }) => {
  return <AgenticWorkflowThread className={className} />;
};

export default WorkflowTimeline;
