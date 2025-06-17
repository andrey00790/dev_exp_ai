import React from 'react';
import { Tab } from '@headlessui/react';
import {
  CloudArrowDownIcon,
  Cog6ToothIcon,
  ServerStackIcon,
  UserCircleIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';
import DataSourcesSettings from '../components/settings/DataSourcesSettings';
import UserPreferences from '../components/settings/UserPreferences';
import ExternalSystems from '../components/settings/ExternalSystems';
import BudgetDashboard from '../components/BudgetDashboard';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

const tabs = [
  { name: 'Data Sources', icon: ServerStackIcon },
  { name: 'External Systems', icon: Cog6ToothIcon },
  { name: 'Budget & Costs', icon: CurrencyDollarIcon },
  { name: 'User Preferences', icon: UserCircleIcon },
];

export default function Settings() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">⚙️ Settings</h1>
        <p className="text-gray-600 mt-1">
          Manage your data sources, external system connections, budget tracking, and user preferences.
        </p>
      </div>

      <Tab.Group>
        <div className="border-b border-gray-200">
          <Tab.List className="-mb-px flex space-x-8 px-1">
            {tabs.map((tab) => (
              <Tab
                key={tab.name}
                className={({ selected }) =>
                  classNames(
                    'flex items-center space-x-2 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm',
                    selected
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  )
                }
              >
                <tab.icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </Tab>
            ))}
          </Tab.List>
        </div>
        <Tab.Panels className="mt-6">
          <Tab.Panel>
            <DataSourcesSettings />
          </Tab.Panel>
          <Tab.Panel>
            <ExternalSystems />
          </Tab.Panel>
          <Tab.Panel>
            <BudgetDashboard />
          </Tab.Panel>
          <Tab.Panel>
            <UserPreferences />
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}
