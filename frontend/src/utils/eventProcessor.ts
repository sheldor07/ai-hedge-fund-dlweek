import { 
  Event, 
  Order, 
  DailyPerformance, 
  TradeAction, 
  TradingDecision 
} from '../models/types';
import { createOrderFromEvent } from './tradingSystem';

/**
 * Processes simulation events to create orders for execution
 * Focuses on EXECUTION events which should have a tradingDecision
 */
export const processEventsForOrders = (
  events: Event[], 
  executorId: string
): Order[] => {
  // Filter to only execution events with trading decisions
  const executionEvents = events.filter(event => 
    event.type === 'EXECUTION' && 
    event.tradingDecision && 
    !event.completed
  );
  
  // Create orders from these events
  const orders: Order[] = [];
  
  for (const event of executionEvents) {
    try {
      if (event.tradingDecision) {
        const order = createOrderFromEvent(event, executorId);
        orders.push(order);
      }
    } catch (error) {
      console.error('Error creating order from event:', error);
    }
  }
  
  return orders;
};

/**
 * Finds corresponding EXECUTION events for DECISION events
 * Used to link decision-making to actual trade execution
 */
export const linkDecisionsToExecutions = (
  events: Event[]
): Map<string, string> => {
  const decisionToExecutionMap = new Map<string, string>();
  
  // Find all decision events with trading decisions
  const decisionEvents = events.filter(event => 
    event.type === 'DECISION' && 
    event.tradingDecision
  );
  
  // For each decision, find a matching execution with the same stock and action
  for (const decision of decisionEvents) {
    if (!decision.tradingDecision) continue;
    
    const { stock, action } = decision.tradingDecision;
    
    // Find execution events for the same stock and action
    const matchingExecution = events.find(event => 
      event.type === 'EXECUTION' && 
      event.tradingDecision && 
      event.tradingDecision.stock === stock && 
      event.tradingDecision.action === action &&
      event.date === decision.date // Must be on the same day
    );
    
    if (matchingExecution) {
      decisionToExecutionMap.set(decision.id, matchingExecution.id);
    }
  }
  
  return decisionToExecutionMap;
};

/**
 * Groups events by date for easy processing
 */
export const groupEventsByDate = (
  events: Event[]
): Map<string, Event[]> => {
  const eventsByDate = new Map<string, Event[]>();
  
  for (const event of events) {
    if (!eventsByDate.has(event.date)) {
      eventsByDate.set(event.date, []);
    }
    
    eventsByDate.get(event.date)?.push(event);
  }
  
  return eventsByDate;
};

/**
 * Groups orders by date for easy processing
 */
export const groupOrdersByDate = (
  orders: Order[]
): Map<string, Order[]> => {
  const ordersByDate = new Map<string, Order[]>();
  
  for (const order of orders) {
    if (!ordersByDate.has(order.date)) {
      ordersByDate.set(order.date, []);
    }
    
    ordersByDate.get(order.date)?.push(order);
  }
  
  return ordersByDate;
};

/**
 * Extracts trading decisions from events with priority to EXECUTION events
 */
export const extractTradingDecisions = (
  events: Event[]
): TradingDecision[] => {
  // First try to get decisions from execution events
  const executionDecisions = events
    .filter(event => 
      event.type === 'EXECUTION' && 
      event.tradingDecision
    )
    .map(event => event.tradingDecision as TradingDecision);
  
  // If we have execution decisions, use those
  if (executionDecisions.length > 0) {
    return executionDecisions;
  }
  
  // Otherwise fall back to regular decision events
  return events
    .filter(event => 
      event.type === 'DECISION' && 
      event.tradingDecision
    )
    .map(event => event.tradingDecision as TradingDecision);
};